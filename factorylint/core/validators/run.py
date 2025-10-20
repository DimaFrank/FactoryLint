import yaml
from dataset_validator import DatasetValidator
from pipeline_validator import PipelineValidator


if __name__ == "__main__":
    rules = yaml.safe_load(open("config.yml"))

    dataset_validator = DatasetValidator(rules)
    pipeline_validator = PipelineValidator(rules)

    dataset_file_path = "./df-sgbi-general-dev/dataset/DS_ADLS_HILAN_BINARY.json"

    dataset_errors = dataset_validator.validate(dataset_file_path)
    print(f"Dataset errors:", dataset_errors)
