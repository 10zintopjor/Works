import uuid
import csv
import requests
import yaml
from convert import ewtstobo


def write_mapping(bdrc_work_id, op_work_id):
    map_file = "./works/mappings/bdrc.csv"
    with open(map_file, "a") as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow([op_work_id, bdrc_work_id])


def get_meta(bdrc_work_id, op_work_id):
    api_id = f"http://purl.bdrc.io/query/graph/OP_info?R_RES=bdr:{bdrc_work_id}&format=json"
    response = requests.get(api_id)

    if response.status_code != 200:
        return

    content = response.json()
    meta_dict = {}
    meta_dict["id"] = str(op_work_id)

    meta_dict["bdrc-work-id"] = bdrc_work_id
    li = []

    meta_dict["title"] = ewtstobo(content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"][
        "http://www.w3.org/2004/02/skos/core#prefLabel"][0]["value"])

    if "http://www.w3.org/2004/02/skos/core#altLabel" in content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"]:
        for id in content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"]["http://www.w3.org/2004/02/skos/core#altLabel"]:
            li.append(ewtstobo(id["value"]))

    meta_dict["alternative-title"] = li

    meta_dict["author"] = ""

    meta_dict["IsRoot"] = content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"][
        "http://purl.bdrc.io/ontology/core/isRoot"][0]["value"]

    meta_dict["type-definition"] = content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"][
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"][0]["value"]

    meta_dict["language"] = content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"][
        "http://purl.bdrc.io/ontology/core/language"][0]["value"]

    meta_dict["wiki-data-id"] = ""

    meta_dict["instances"] = ""

    return meta_dict


def write_works(bdrc_work_id, op_work_id):
    meta_content = get_meta(bdrc_work_id, op_work_id)
    yml_file = f"./yaml/{op_work_id}.yml"
    if meta_content is None:
        return
    with open(yml_file, "w") as file:
        yaml.dump(meta_content, file, sort_keys=False,
                  default_flow_style=False)


if __name__ == "__main__":
    file_path = "clusters-manual.csv"
    with open(file_path, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            op_work_id = uuid.uuid4()
            print(op_work_id)
            #write_mapping(row[1], op_work_id)
            write_works(row[1], op_work_id)
