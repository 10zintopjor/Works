from uuid import uuid4
import csv
import requests
import yaml
from convert import ewtstobo

class MyDumper(yaml.Dumper):

    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)


def represent_none(self, _):
    return self.represent_scalar('tag:yaml.org,2002:null', '')


def write_mapping(op_work_id,bdrc_work_id):
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

    if isavailable("http://www.w3.org/2004/02/skos/core#prefLabel",content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"]) == True:
        title = ewtstobo(content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"]["http://www.w3.org/2004/02/skos/core#prefLabel"][0]["value"])
        meta_dict["title"] = title
    else:
        meta_dict["title"] = None

    if isavailable("http://www.w3.org/2004/02/skos/core#altLabel",content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"])==True:
        for id in content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"]["http://www.w3.org/2004/02/skos/core#altLabel"]:
            li.append(ewtstobo(id["value"]))

    if not li:
        meta_dict["alternative-title"]=None
    else:
        meta_dict["alternative-title"] = li

    meta_dict["author"] = None

    if isavailable("http://purl.bdrc.io/ontology/core/isRoot",content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"]) == True:
        value = content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"]["http://purl.bdrc.io/ontology/core/isRoot"][0]["value"]
        print(value)
        meta_dict["isRoot"]= value.strip("'")
    else:
        meta_dict["isRoot"] = None

    if isavailable("http://www.w3.org/1999/02/22-rdf-syntax-ns#type",content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"]) == True:    
        meta_dict["type-definition"] = content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"]["http://www.w3.org/1999/02/22-rdf-syntax-ns#type"][0]["value"]
    else:
        meta_dict["type-definition"] = None

    if isavailable("http://purl.bdrc.io/ontology/core/language",content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"]) ==True:
        meta_dict["language"] = content[f"http://purl.bdrc.io/resource/{bdrc_work_id}"][
            "http://purl.bdrc.io/ontology/core/language"][0]["value"]

    meta_dict["wiki-data-id"] = None

    meta_dict["instances"] = None

    return meta_dict

def isavailable(param,body):
    if param in body:
        return True
    else:
        return False    

def write_works(bdrc_work_id, op_work_id):
    meta_content = get_meta(bdrc_work_id, op_work_id)
    yaml.add_representer(type(None), represent_none)

    yml_file = f"./yaml/{op_work_id}.yml"
    if meta_content is None:
        return
    with open(yml_file, "w", encoding = "utf-8") as file:
        yaml.dump(meta_content, file,Dumper=MyDumper,sort_keys=False,
                  default_flow_style=False, allow_unicode = True)

def get_uuid():
    return uuid4().hex

if __name__ == "__main__":
    file_path = "clusters-manual.csv"
    with open(file_path, "r") as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            op_work_id = get_uuid()
            write_mapping(op_work_id,row[1])
            write_works(row[1], op_work_id)
            print("pass")
