import yaml

config = yaml.safe_load(open("config.yml"))
rules = config["resources"]["datasets"]["naming"]

print(rules)