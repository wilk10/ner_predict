from modules.apis import Apis


class Normalization:
    NOMENCLATURE_BY_KINGDOM = {'plant': 'EPPO Global Database', 'animal': 'Catalogue of Life'}
    ANIMAL_CONVERSIONS = {
        'domestic cat': ['cat', 'feline'], 'canis lupus familiaris': ['dog', 'canine'], 'human': ['patient', 'person'],
        'horse': ['equine'], 'domestic goat': ['goat'], 'sus scrofa': ['pig'], 'ovis aries': ['sheep']}
    ACCEPTED_LANGUAGES = ['english', 'latin', 'en', 'la']

    def __init__(self):
        self.apis = Apis()

    def get_eppo_code(self, entity):
        concept_id = None
        response = self.apis.call('eppo', entity)
        if response is not None:
            latin_or_english_names = [result for result in response if result['lang'] in ['la', 'en']]
            if latin_or_english_names:
                concept_id = latin_or_english_names[0]['eppocode']
        return concept_id

    @staticmethod
    def find_matching_full_version_entity(text, entity):
        for char in ['.', ',', ':', ';', '(', ')', '[', ']']:
            text = text.replace(char, '')
        full_version_entity = None
        entity_words = entity.lower().split()
        text_words = text.lower().split()
        for j, word in enumerate(text_words):
            if word == entity_words[-1] and j != 0:
                previous_word = text_words[j-1]
                if previous_word[0] == entity_words[0][0] and len(previous_word) > 2:
                    full_version_entity = ' '.join([previous_word, entity_words[-1]])
        return full_version_entity

    def get_possible_animal_entities(self, entity):
        entity = entity.strip().lower()
        without_s = entity[:-1] if entity[-1] == 's' else entity
        final_entities = []
        for ent in {entity, without_s}:
            alternative_names = [name for name, inputs in self.ANIMAL_CONVERSIONS.items() if ent in inputs]
            if alternative_names:
                final_entities.extend(alternative_names)
            else:
                final_entities.append(ent)
        return final_entities

    def get_concept_id(self, entity, bioconcept, text):
        if bioconcept == 'PLANT_SPECIES':
            concept_id = self.get_eppo_code(entity)
            if concept_id is None:
                entity_words = entity.split()
                if len(entity_words) == 2 and entity_words[0][1] == '.':
                    full_entity = self.find_matching_full_version_entity(text, entity)
                    if full_entity is not None:
                        concept_id = self.get_eppo_code(full_entity)
        else:
            assert bioconcept == 'TARGET_SPECIES'
            concept_id = None
            possible_entities = self.get_possible_animal_entities(entity)
            id_found = False
            for possible_entity in possible_entities:
                response = self.apis.call('cat_life', possible_entity)
                if 'results' in response.keys():
                    for result in response['results']:
                        if possible_entity == result['name'].lower():
                            if result['name_status'] == 'accepted name':
                                if 'id' in result.keys():
                                    concept_id = result['id']
                                    id_found = True
                            elif 'language' in result.keys() and 'accepted_name' in result.keys():
                                if result['language'].lower() in self.ACCEPTED_LANGUAGES:
                                    if 'id' in result['accepted_name']:
                                        concept_id = result['accepted_name']['id']
                                        id_found = True
                            if id_found:
                                break
                if id_found:
                    break
        return concept_id

    def get_item_classifications(self, predictions, item_text, kingdom):
        item_classifications = []
        for prediction in predictions:
            bioconcept = prediction['tag'].upper()
            if bioconcept in ['PLANT_SPECIES', 'TARGET_SPECIES']:
                named_entity = item_text[prediction['start']:prediction['end']]
                if named_entity not in [c['named_entity'] for c in item_classifications]:
                    concept_id = self.get_concept_id(named_entity, bioconcept, item_text)
                    if concept_id is not None:
                        if concept_id not in [c['conceptID'] for c in item_classifications]:
                            classification = {
                                'named_entity': named_entity,
                                'Nomenclature': self.NOMENCLATURE_BY_KINGDOM[kingdom],
                                'conceptID': concept_id}
                            item_classifications.append(classification)
        for classification in item_classifications:
            del classification['named_entity']
        return item_classifications
