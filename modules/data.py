import os
import json
import pandas
import pathlib


class Data:
    KINGDOMS = ['animal', 'plant']
    BIOCONCEPTS_BY_KINGDOM = {
        'plant': ['PLANT_PEST', 'PLANT_SPECIES', 'PLANT_DISEASE_COMMNAME'],
        'animal': ['PATHOGENIC_ORGANISMS', 'TARGET_SPECIES', 'LOCATION', 'PREVALENCE', 'YEAR', 'ANMETHOD']}
    EXTENSIONS = ['.txt', '.json']
    PROPER_TABS_BY_KINGDOM = {
        'animal': ['Abstract', 'Refid', 'Title', 'content'],
        'plant': ['Refid', 'Author', 'Title', 'content']}
    TABS_ERROR_MESSAGE = 'one or more of the proper tab names {} do not appear in your txt file tabs {}'

    def __init__(self, inputs_dir: pathlib.Path, results_dir: pathlib.Path):
        self.inputs_dir = inputs_dir
        self.results_dir = results_dir
        self.bioconcepts = [bc for kingdom, bioconcepts in self.BIOCONCEPTS_BY_KINGDOM.items() for bc in bioconcepts]
        self.output_filename_by_kingdom = self.get_output_filenames()

    def get_output_filenames(self):
        output_filename_by_kingdom = dict.fromkeys(self.KINGDOMS)
        for kingdom in self.KINGDOMS:
            file_paths_by_extension = self.list_relevant_file_paths(kingdom)
            if len(file_paths_by_extension['.txt']) == 1:
                filename = file_paths_by_extension['.txt'][0].name
                output_filename = filename.replace('txt', 'json')
            else:
                output_filename = f'{kingdom}_output_file.json'
            output_filename_by_kingdom[kingdom] = output_filename
        return output_filename_by_kingdom

    def list_relevant_file_paths(self, kingdom):
        kingdom_dir = self.inputs_dir / kingdom
        files = os.listdir(str(kingdom_dir))
        return {extension: [kingdom_dir / file for file in files if extension in file] for extension in self.EXTENSIONS}

    def check_txt_tab_names(self, df, kingdom):
        proper_tabs = self.PROPER_TABS_BY_KINGDOM[kingdom]
        error_message = self.TABS_ERROR_MESSAGE.format(proper_tabs, df.columns.values)
        assert all([proper_tab in df.columns.values for proper_tab in proper_tabs]), error_message

    @staticmethod
    def format_single_item_from_df(row, kingdom):
        item = {'example': {'metadata': {}}, 'results': {'annotations': [], 'classifications': []}}
        if kingdom == 'animal':
            metadata = {
                'Abstract': row.Abstract, 'Refid': row.Refid, 'Author': '', 'Title': row.Title}
        else:
            if len(row.content.split(' | ')) > 1:
                text = ''.join(row.content.split(' | ')[1:])
            else:
                text = row.content
            metadata = {'Refid': row.Refid, 'Author': row.Author, 'text': text, 'Title': row.Title}
        item['example']['metadata'] = metadata
        item['example']['content'] = row.content
        return item

    @staticmethod
    def load_json(file_path):
        with open(str(file_path), encoding='utf-8') as f:
            data = json.load(f)
        return data

    @staticmethod
    def save_json(file_path, data):
        with open(str(file_path), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_prediction_data(self):
        data_by_kingdom = dict.fromkeys(self.KINGDOMS)
        for kingdom in self.KINGDOMS:
            data = {'result': []}
            file_paths_by_extension = self.list_relevant_file_paths(kingdom)
            for extension, file_paths in file_paths_by_extension.items():
                for file_path in file_paths:
                    if extension == '.txt':
                        df = pandas.read_table(file_path, encoding='latin-1')
                        self.check_txt_tab_names(df, kingdom)
                        for _, row in df.iterrows():
                            item = self.format_single_item_from_df(row, kingdom)
                            data['result'].append(item)
                    else:
                        file_data = self.load_json(file_path)
                        assert 'result' in file_data.keys(), 'there is no "result" key in the input file'
                        for file_item in file_data['result']:
                            assert 'example' in file_item.keys(), 'there is no "example" key in this item'
                            assert 'content' in file_item['example'].keys(), 'there is no "content" key in this item'
                            data['result'].append(file_item)
            data_by_kingdom[kingdom] = data
        return data_by_kingdom
