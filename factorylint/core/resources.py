import enum

class ResourceType(enum.Enum):
    DATASET = "datasets"
    LINKED_SERVICE = "linked_services"
    PIPELINE = "pipelines"
    TRIGGER = "triggers"
    INTEGRATION_RUNTIME = "integration_runtimes"
