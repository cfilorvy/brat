import os
import time

from annotation import Annotations, SimpleAnnotations, TextAnnotations
from document import real_directory
from folia2brat import get_extra_info
from projectconfig import ProjectConfiguration
from verify_annotations import verify_annotation

try:
    from cPickle import dump as pickle_dump, load as pickle_load
except ImportError:
    from pickle import dump as pickle_dump, load as pickle_load

from config import WORK_DIR
from message import Messager
import session
import simplejson as json


def filter_layers(ann,path):
     #Added by Sander Naert to disable the visualisation of same annotations
    try:
        string = session.load_conf()["config"]
        val = json.loads(string)["layers"]
    except session.NoSessionError:
        val = []
    except KeyError:
        val = []
    except Exception as e:
        val = []
        Messager.error("Error while enabling/disabling layers: "+str(e))
    proj = ProjectConfiguration(path)
    forbidden_entities = set()
    forbidden_ann=[]
    for i in val:
        forbidden_ann.append(i)        
    temp_array = []
    
    #Remove forbidden entities
    for i in ann["entities"]:
        if i[1] in forbidden_ann:
            forbidden_entities.add(i[0])
        else:
            temp_array.append(i)
    ann["entities"] = temp_array

    #Remove forbidden triggers
    temp_array = []
    forbidden_events=[]
    for i in ann["triggers"]:
        if i[1] in forbidden_ann:
            forbidden_events.append(i[0])
        else:
            temp_array.append(i)
    ann["triggers"] = temp_array
    
    #Remove forbidden events
    temp_array = []
    for i in ann["events"]:
        if i[1] in forbidden_events:
            pass
        else:
            #delete references to removed entities
            i[2][:] = [ role for role in i[2] if not role[1] in forbidden_entities ]
            temp_array.append(i)
    ann["events"] = temp_array
    
    #Remove forbidden relations
    temp_array = []
    for i in ann["relations"]:
        if i[1] in forbidden_ann:
            pass
        else:
            #if an arg points to an forbidden_ent then also remove this relation
            roles = [ role for role in i[2] if role[1] in forbidden_entities ]
            if not roles:
                temp_array.append(i)
    ann["relations"] = temp_array
    
    #Remove forbidden attributes
    temp_array = []
    for i in ann["attributes"]:
        if i[1] in forbidden_ann:
            pass
        elif not i[2] in forbidden_entities:
                temp_array.append(i)
    ann["attributes"] = temp_array
    
    return ann


def filter_folia(ann_obj):
    response = {"entities":[],"comments":[],"relations":[],"attributes":[],"tokens":{}}
    try:
        string = session.load_conf()["config"]
        val = json.loads(string)["foliaLayers"]
    except session.NoSessionError:
        val = []
    except KeyError:
        val = []
        pass
    except Exception as e:
        val = []
        Messager.error("Error while enabling/disabling folia layers: "+str(e))
        pass
    try:
        response["tokens"]=ann_obj.folia["tokens"]
    except KeyError as e:
        pass
    if val:
        removed = set()
        forbidden = set(i for i in val)
        result = []
        alternatives = "alter" in val
        try:
            if 'all' in val:
                response["tokens"]={}
                return response
            else:
                for i in ann_obj.folia["entities"]:
                    if not i[3] in forbidden and not ( i[4] and alternatives ):
                        result.append(i)
                    else:
                        removed.add(i[0])
                response["entities"] = result
                result = []
                for i in ann_obj.folia["relations"]:
                    if not i[3] in forbidden and not i[2][0][1] in removed and not i[2][1][1] in removed and not ( i[4] and alternatives ):
                        result.append(i)
                    else:
                        removed.add(i[0])
                response["relations"] = result
                result = []
                for i in ann_obj.folia["attributes"]:
                    if not i[2] in removed:
                        result.append(i)
                response["attributes"] = result
                result = []
                for i in ann_obj.folia["comments"]:
                    if not i[0] in removed:
                        result.append(i)
                response["comments"] = result
        except KeyError:
            pass
    else:
        response = ann_obj.folia
    return response
    
    
def getAnnObject(collection,document):
    try:
        real_dir = real_directory(collection)
    except:
        real_dir=collection      
    app_path = WORK_DIR + "/application/"
    full_name = collection + document
    full_name = full_name.replace("/","")
    if(os.path.isfile(app_path+full_name)):
        temp=open (app_path+full_name , 'rb')
        ann = pickle_load(temp)
        temp.close()
    else:
        ann = TextAnnotations(real_dir+document)
        ann = SimpleAnnotations(ann)
        ann.folia = {}
        try:
            #TODO:good error message
            ann.folia=get_extra_info(collection,document)
        except Exception as e:
            ann.folia = {}
            Messager.error('Error: get extra folia info() failed: %s' % e)
    #Validation:
    try:
        docdir = os.path.dirname(ann._document)
        string = session.load_conf()["config"]
        val = json.loads(string)["validationOn"]
        #validate if config enables it and if it's not already done.
        if val:
            if not ann.validated:
                projectconf = ProjectConfiguration(docdir)
                issues = verify_annotation(ann, projectconf)
            else:
                issues = ann.issues
        else:
            ann.validated = False
            issues = []
    except session.NoSessionError:
        issues = []
    except KeyError:
        issues = []
    except Exception as e:
        # TODO add an issue about the failure?
        issues = []
        Messager.error('Error: validation failed: %s' % e)
    ann.issues = issues
    temp=open (app_path+full_name , 'wb')    
    pickle_dump(ann, temp)
    temp.close()
    return ann

    
def update_pickle(sann):
    app_path = WORK_DIR + "/application/"
    temp_paths = sann.get_document().split("/data/")
    try:
        full_name = temp_paths[1].replace("/","")
        temp=open (app_path+full_name , 'wb')
        pickle_dump(sann, temp)
        temp.close()
    except Exception as e:
        Messager.error("Error while caching changes in the annotation file: "+str(e))


def update_dump(j_dic,file_path):
    app_path = WORK_DIR + "/application/"
    temp_paths = file_path.split("/data/")
    try:
        full_name = temp_paths[1].replace("/","")
        temp=open (app_path+full_name , 'wb')
        pickle_dump(j_dic, temp)
        temp.close()
    except Exception as e:
        Messager.error("Error while caching changes in the annotation file: "+str(e))
        
    
if __name__ == '__main__':
    millis = int(round(time.time() * 1000))
    print millis
    ann = Annotations("/home/sander/Documents/Masterproef/brat/data/test")
    sann = SimpleAnnotations(ann)
    print filter_folia(sann)
    millis = int(round(time.time() * 1000)) - millis
    print millis
