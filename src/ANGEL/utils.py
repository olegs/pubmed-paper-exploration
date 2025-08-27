import torch
import pickle
import argparse
from transformers import BartForConditionalGeneration, BartTokenizer, BartConfig
from src.ANGEL.models import BartEntityPromptModel
from collections import defaultdict
import json
from tqdm import tqdm
import random
import ast
from datasets import Dataset
from src.ANGEL.trie import Trie
from src.config.config import config as file_config

def load_dictionary(config):
    
    print('loading dictionary....')
    dict_path = config.dict_path
    if 'json' in dict_path:
        with open(dict_path, 'r') as f:
            cui2str = json.load(f)
    else:
        with open(dict_path, 'rb') as f:
            cui2str = pickle.load(f)

    str2cui = {}
    for cui in cui2str:
        if isinstance(cui2str[cui], list):
            for name in cui2str[cui]:
                if name in str2cui:
                    str2cui[name].append(cui)
                else:
                    str2cui[name] = [cui]
        else:
            name = cui2str[cui]
            if name in str2cui:
                str2cui[name].append(cui)
                print('duplicated vocabulary')
            else:
                str2cui[name] = [cui]
    print('dictionary loaded......')
    
    return cui2str, str2cui
    
def load_trie(config):
    
    print('loading trie......')
    with open(config.trie_path, "rb") as f:
        trie = Trie.load_from_dict(pickle.load(f))

    return trie

def load_cui_label(config):
    
    print('loading cui labels......')
    with open(config.dataset_path+f'/{["test" if config.testset else "dev"][0]}label.txt', 'r') as f:
        cui_labels = [set(cui.strip('\n').replace('+', '|').split('|')) for cui in f.readlines()]

    return cui_labels

def convert_sets_to_lists(obj):
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, list):
        return [convert_sets_to_lists(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_sets_to_lists(value) for key, value in obj.items()}
    else:
        return obj

def load_label_ft(config, set_type):
    
    print(f'loading {set_type} label cuis......')
    with open(config.dataset_path+f'/{set_type}label.txt', 'r') as f:
        cui_labels = [set(cui.strip('\n').replace('+', '|').split('|')) for cui in f.readlines()]
    print(f'{set_type} label cuis loaded')

    return cui_labels

def reform_input(inputs, attention_mask = None, ending_token = 2):
    
    ## input a tensor of size BSZ x Length
    max_idx = torch.max(torch.where(inputs==ending_token)[1])
    inputs = inputs[:, :max_idx+1]
    if attention_mask is not None:
        attention_mask = attention_mask[:, :max_idx+1]

    return inputs, attention_mask

def read_file_bylines(file):
    with open(file, 'r') as f:
        lines = f.readlines()
    output = []
    for item in lines[:]:
        output.append(ast.literal_eval(item.strip('\n')))
    return output

def load_model(config, dpo=False):

    tokenizer = BartTokenizer.from_pretrained('facebook/bart-large', max_length=1024)
    bartconf = BartConfig.from_pretrained(config.model_load_path)
    
    if dpo:
        model = BartForConditionalGeneration.from_pretrained(config.model_load_path, config = bartconf)
    else:
        model = BartEntityPromptModel.from_pretrained(config.model_load_path, 
                                                        config = bartconf,
                                                        n_tokens = (config.prompt_tokens_enc, config.prompt_tokens_dec), 
                                                        load_prompt = True, 
                                                        soft_prompt_path=config.model_load_path,
                                                        use_safetensors=True
                                                        )
    return model, tokenizer

def convert_sets_to_lists(obj):
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, list):
        return [convert_sets_to_lists(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_sets_to_lists(value) for key, value in obj.items()}
    else:
        return obj


default_config = {
  "dataset_path": None,
  "dpo_dataset_path": None,
  "model_name": "ncbi",
  "dataset": "",
  "model_save_path": "./model_saved",
  "model_load_path": "facebook/bart-large",
  "model_token_path": "facebook/bart-large",
  "trie_path": "./trie.pkl",
  "dict_path": "./benchmark/ncbi_EL/target_kb.json",
  "retrieved_path": "./trie.pkl",
  "output_path": "./output",
  "logging_path": "./logs",
  "logging_steps": 1000,
  "save_steps": 20000,
  "eval_steps": 500,
  "num_train_epochs": 8,
  "per_device_train_batch_size": 4,
  "per_device_eval_batch_size": 1,
  "warmup_steps": 500,
  "max_grad_norm": 0.1,
  "max_steps": 20000,
  "gradient_accumulate": 1,
  "weight_decay": 0.01,
  "init_lr": 5e-05,
  "lr_scheduler_type": "polynomial",
  "evaluation_strategy": "no",
  "num_beams": 5,
  "length_penalty": 1.0,
  "beam_threshold": 0.0,
  "max_length": 1024,
  "min_length": 1,
  "attention_dropout": 0.1,
  "dropout": 0.1,
  "rdrop": 0.0,
  "label_smoothing_factor": 0.1,
  "unlikelihood_loss": False,
  "unlikelihood_weight": 0.1,
  "max_position_embeddings": 1024,
  "prompt_tokens_enc": 0,
  "prompt_tokens_dec": 0,
  "make_all_pair": False,
  "finetune": False,
  "t5": False,
  "fairseq_loss": False,
  "evaluation": False,
  "testset": False,
  "load_prompt": False,
  "sample_train": False,
  "prefix_prompt": False,
  "init_from_vocab": False,
  "rerank": False,
  "no_finetune_decoder": False,
  "syn_pretrain": False,
  "new_dpo_method": False,
  "gold_sty": False,
  "prefix_mention_is": False,
  "num_epochs": 1,
  "beta": 0.1,
  "dpo_topk": 10,
  "wandb": False,
  "sweep": False,
  "hard_negative": False,
  "debug": False,
  "local_rank": 0,
  "seed": 0
}

class ConfigObject:
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
            
def get_config():
    config = ConfigObject(default_config)
    config.model_load_path = file_config.angel_config["model_load_path"]
    config.model_token_path = file_config.angel_config["model_token_path"]
    config.per_device_eval_batch_size = file_config.angel_config["per_device_eval_batch_size"]
    config.num_beams = file_config.angel_config["num_beams"]
    config.prefix_mention_is = file_config.angel_config["prefix_mention_is"]
    return config