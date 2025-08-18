import os
import sys
from functools import lru_cache

import numpy as np
from tqdm import tqdm
import pickle
import argparse

import torch 
import torch.nn as nn
from transformers import TrainingArguments
from src.ANGEL.trainer import modifiedSeq2SeqTrainer
from src.ANGEL.trie import Trie
from src.ANGEL.utils import (reform_input, 
                   get_config, 
                   load_dictionary, 
                   load_trie, 
                   load_cui_label,
                   read_file_bylines,
                   convert_sets_to_lists
                   )
import copy
import json
# import wandb
import ast
from src.ANGEL.fairseq_beam import SequenceGenerator, PrefixConstrainedBeamSearch, PrefixConstrainedBeamSearchWithSampling
from src.ANGEL.models import BartEntityPromptModel
from transformers import BartTokenizer, BartConfig
from src.ANGEL.datagen import prepare_trainer_dataset, process_sample  

tokenizer = None
bartconf = None
model = None


@lru_cache
def load_candidate_trie(candidates):
    global tokenizer
    return Trie.load_from_dict(Trie([16]+list(tokenizer(' ' + candidate.lower())['input_ids'][1:]) for candidate in tqdm(candidates)).trie_dict)




def run_sample(config, input_sentence, prefix_sentence, candidates):
    global tokenizer
    global bartconf
    global model

    tokenizer = tokenizer or BartTokenizer.from_pretrained(config.model_token_path)
    bartconf = bartconf or BartConfig.from_pretrained(config.model_load_path)
    bartconf.max_position_embeddings = config.max_position_embeddings
    bartconf.attention_dropout = config.attention_dropout
    bartconf.dropout = config.dropout
    bartconf.max_length = config.max_length

    model = model or BartEntityPromptModel.from_pretrained(config.model_load_path, 
                                                    config = bartconf,
                                                    n_tokens = (config.prompt_tokens_enc, config.prompt_tokens_dec), 
                                                    load_prompt = True, 
                                                    soft_prompt_path=config.model_load_path
                                                    )
    model = model.cuda().to(model.device)        
    trie = load_candidate_trie(tuple(candidates))
            
    eval_dataset = process_sample(
        [list(tokenizer(' '+input_sentence)['input_ids'])[1:-1]], 
        [list(tokenizer(' '+prefix_sentence)['input_ids'])[1:-1]]
        )
        
    beam_strategy = PrefixConstrainedBeamSearch(
        tgt_dict=None, 
        prefix_allowed_tokens_fn=lambda batch_id, sent: trie.get(sent.tolist())
    )
    
    fairseq_generator = SequenceGenerator(
        models = model,
        tgt_dict = None,
        beam_size=config.num_beams,
        max_len_a=0,
        max_len_b=config.max_length,
        min_len=config.min_length,
        eos=model.config.eos_token_id,
        search_strategy=beam_strategy,

        ##### all hyperparams below are set to default
        normalize_scores=True,
        len_penalty=config.length_penalty,
        unk_penalty=0.0,
        temperature=0.7,
        match_source_len=False,
        no_repeat_ngram_size=0,
        symbols_to_strip_from_output=None,
        lm_model=None,
        lm_weight=1.0,
    )
    
    input_ids = eval_dataset[0]['input_ids'].unsqueeze(0)
    attention_mask = eval_dataset[0]['attention_mask'].unsqueeze(0)
    decoder_input_ids = [eval_dataset[0]['decoder_input_ids_test']]
    sample = {'net_input':{'input_ids':input_ids, 'attention_mask':attention_mask}}

    result_tokens, posi_scores = fairseq_generator.forward(
        sample=sample,
        prefix_mention_is = config.prefix_mention_is,
        prefix_tokens=decoder_input_ids[0].unsqueeze(0).cuda() if config.prefix_mention_is else None,
    )
    
    for ba, beam_sent in enumerate(result_tokens):
        result = []
        for be, sent in enumerate(beam_sent):
            if config.prefix_mention_is:
                result.append(tokenizer.decode(sent[len(decoder_input_ids[0]):], skip_special_tokens=True))
            else:
                result.append(tokenizer.decode(sent, skip_special_tokens=True))
                
                
    #print(f"\nInput  : {tokenizer.decode(input_ids[0], skip_special_tokens=True)}")  
    #print(f"Output : {tokenizer.decode(decoder_input_ids[0])}{result[0]}")      
    return result[0]

if __name__ == '__main__':
    
    config = get_config()
        
    # Input question and prefix
    input_sentence = "START normal cells of the uterine cervix art12355 END"
    prefix_sentence = "normal cells of the uterine cervix art12355 is"
    
    # Input your Candidates
    candidates = ["adrenoleukodystrophy", "thrombosis", "anemia", "huntington disease", "leukodystrophy metachromatic", "uterine cervix", "cells", "atypical squamous cells of the cervix", "neuroectoderm", "neuroepithelial cells", "fibroblast", "sa79", "adipocyte", "system asc transporter"]
    
    run_sample(config, input_sentence, prefix_sentence, candidates)


