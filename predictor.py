import pathlib
import argparse
from modules.data import Data
from modules.normalization import Normalization
from modules.deep_learning import DeepLearning


class Predictor:
    MODELS_DIR_NAME = 'models'
    RESULTS_DIR_NAME = 'results'
    INPUTS_DIR_NAME = 'input_files'

    def __init__(self, normalize: bool):
        self.normalize = normalize
        self.cwd = pathlib.Path.cwd()
        self.models_dir = self.cwd / self.MODELS_DIR_NAME
        self.results_dir = self.cwd / self.RESULTS_DIR_NAME
        self.inputs_dir = self.cwd / self.INPUTS_DIR_NAME
        self.data = Data(self.inputs_dir, self.results_dir)
        self.normalisation = Normalization()
        self.deep_learning = DeepLearning(self.models_dir, self.data.bioconcepts)
        self.data_by_kingdom = self.data.get_prediction_data()

    @staticmethod
    def format_prediction(prediction):
        if prediction['tag'] == 'ANMETHOD':
            final_tag = 'AnMethod'
        else:
            lower_tag = prediction['tag'].lower()
            final_tag = lower_tag[0].upper() + lower_tag[1:]
        return {'start': prediction['start'], 'end': prediction['end'], 'tag': final_tag}

    def run(self):
        for kingdom in self.data.KINGDOMS:
            kingdom_data = self.data_by_kingdom[kingdom]
            for i, item in enumerate(kingdom_data['result']):
                item_text = item['example']['content']
                predictions = self.deep_learning.make_predictions(kingdom, item_text)
                print(f'item {i} of {kingdom}s predicted')
                formatted_predictions = [self.format_prediction(prediction) for prediction in predictions]
                kingdom_data['result'][i]['results']['annotations'] = formatted_predictions
                if self.normalize:
                    item_classifications = self.normalisation.get_item_classifications(predictions, item_text, kingdom)
                    kingdom_data['result'][i]['results']['classifications'] = item_classifications
            output_filename = self.data.output_filename_by_kingdom[kingdom]
            file_path = self.results_dir / output_filename
            self.data.save_json(file_path, kingdom_data)
            print(f'final json file save to {file_path}')


def parse_arguments():
    normalization_help = 'add to perform species normalization'
    parser = argparse.ArgumentParser()
    parser.add_argument('--normalize', dest='normalize', action='store_true', default=False, help=normalization_help)
    return parser.parse_args()


if __name__ == '__main__':
    arguments = parse_arguments()
    Predictor(**vars(arguments)).run()
