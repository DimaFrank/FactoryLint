import yaml
from factorylint.core.validators import DatasetValidator, PipelineValidator, LinkedServiceValidator, TriggerValidator

if __name__ == "__main__":
    rules = yaml.safe_load(open("config.yml"))

    dataset_validator = DatasetValidator(rules)
    pipeline_validator = PipelineValidator(rules)
    linked_service_validator = LinkedServiceValidator(rules)
    trigger_validator = TriggerValidator(rules)


    dataset_file_path = "./df-sgbi-general-dev/dataset/LS_ADLS_ITBM_PARQUET.json"
    dataset_errors = dataset_validator.validate(dataset_file_path)
    print(f"Dataset errors:", dataset_errors)


    pipeline_file_path = "./df-sgbi-general-dev/pipeline/001_01_MES_IoT_daily.json"
    pipeline_errors = pipeline_validator.validate(pipeline_file_path)
    print(f"Pipeline errors:", pipeline_errors)


    linkedservice_file_path = "./df-sgbi-general-dev/linkedService/LS_DATAV_APP.json"
    linkedservice_errors = linked_service_validator.validate(linkedservice_file_path)
    print(f"Linked Service errors:", linkedservice_errors)

    trigger_file_path = "./df-sgbi-general-dev/trigger/Daily-MES-UpdateYields.json"
    trigger_errors = trigger_validator.validate(trigger_file_path)
    print(f"Trigger errors:", trigger_errors)