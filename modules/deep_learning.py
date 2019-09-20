import re
import spacy
import pathlib
from modules.data import Data


class DeepLearning:
    BIOCONCEPTS_FOR_PARTIAL_INITIALISATION = [
        'PLANT_PEST', 'PLANT_SPECIES', 'PLANT_DISEASE_COMMNAME', 'PATHOGENIC_ORGANISMS', 'TARGET_SPECIES', 'ANMETHOD']

    def __init__(self, models_dir: pathlib.Path, bioconcepts: list):
        self.models_dir = models_dir
        self.bioconcepts = bioconcepts
        self.model_dir_by_bioconcept = {bc: self.models_dir / bc.lower() for bc in self.bioconcepts}

    @staticmethod
    def find_matches_and_make_annotations(entry, text, bioconcept):
        entry = entry.replace('.', '\.')
        try:
            matches = [match for match in re.finditer(entry, text)]
        except re.error:
            matches = []
        annotations = []
        for match in matches:
            annotation = {'tag': bioconcept, 'start': match.start(), 'end': match.end()}
            annotations.append(annotation)
        return annotations

    @classmethod
    def add_partial_initials(cls, input_noun, text, bioconcept, annotations):
        noun_chunks = input_noun.split(' ')
        more_entities = []
        if len(noun_chunks) > 1:
            for i, this_chunk in enumerate(noun_chunks):
                if '(' not in this_chunk and ')' not in this_chunk:
                    initialised_chunk = this_chunk[0] + '.'
                    new_chunks = noun_chunks[:i] + [initialised_chunk] + noun_chunks[i + 1:]
                    partially_initialised_noun = ' '.join(new_chunks)
                    more_entities.append(partially_initialised_noun)
        for entity in more_entities:
            new_annotations = cls.find_matches_and_make_annotations(entity, text, bioconcept)
            annotations.extend(new_annotations)
        return annotations

    @staticmethod
    def clean_annotations(annotations):
        sorted_annotations = sorted(annotations, key=lambda a: a['start'])
        cleaned_annotations = [sorted_annotations[0]]
        for i, annotation in enumerate(sorted_annotations[1:]):
            previous_annotation = cleaned_annotations[-1]
            if annotation['start'] > previous_annotation['end']:
                cleaned_annotations.append(annotation)
            else:
                annotation_length = annotation['end'] - annotation['start']
                previous_length = previous_annotation['end'] - previous_annotation['start']
                if annotation_length > previous_length:
                    cleaned_annotations[-1] = annotation
        return cleaned_annotations

    def make_predictions(self, kingdom, item_text):
        predictions = []
        for bioconcept in Data.BIOCONCEPTS_BY_KINGDOM[kingdom]:
            model_dir = self.model_dir_by_bioconcept[bioconcept]
            bioconcept_nlp = spacy.load(model_dir)
            doc = bioconcept_nlp(item_text)
            bioconcept_predictions = []
            for entity in doc.ents:
                entity_predictions = self.find_matches_and_make_annotations(entity.text, item_text, bioconcept)
                bioconcept_predictions.extend(entity_predictions)
                if bioconcept in self.BIOCONCEPTS_FOR_PARTIAL_INITIALISATION:
                    bioconcept_predictions = self.add_partial_initials(
                        entity.text, item_text, bioconcept, bioconcept_predictions)
            predictions.extend(bioconcept_predictions)
        if predictions:
            predictions = self.clean_annotations(predictions)
        return predictions
