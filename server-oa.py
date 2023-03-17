import torch
from torch import nn
from torch.nn import functional as F
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import StoppingCriteria, StoppingCriteriaList
from fastapi import Request, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from types import SimpleNamespace

base_path = 'OpenAssistant/oasst-sft-1-pythia-12b'
# base_path = 'Rallio67/chip_12B_instruct_alpha'
chip_map = {'gpt_neox.embed_in': 0,
            'gpt_neox.layers': 0,
            'gpt_neox.final_layer_norm': 0,
            'embed_out': 0}

model = AutoModelForCausalLM.from_pretrained(
    base_path, load_in_8bit=True, device_map=chip_map,
    torch_dtype=torch.float16, offload_state_dict=True
)
tokenizer = AutoTokenizer.from_pretrained(base_path)
origins = [
    "*",
]

# stop words


class KeywordsStoppingCriteria(StoppingCriteria):
    def __init__(self, keywords_ids: list):
        self.keywords = keywords_ids

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        if input_ids[0][-1] in self.keywords:
            return True
        return False


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate(prompt):
    params = SimpleNamespace()
    params.stopWords = ["<|endoftext|>"]
    stop_words = params.stopWords
    stop_ids = [tokenizer.encode(w)[0] for w in stop_words]
    stop_criteria = KeywordsStoppingCriteria(stop_ids)
    # batch = tokenizer.encode(prompt, return_tensors="pt")
    encoded_input = tokenizer(prompt, return_tensors='pt')
    out = model.generate(
        input_ids=encoded_input['input_ids'].cuda(0),
        do_sample=True,
        num_beams=1,
        use_cache=False,
        eos_token_id=0,
        pad_token_id=0,
        max_new_tokens=5,
        num_return_sequences=1,
        # stopping_criteria=StoppingCriteriaList([stop_criteria]),
        temperature=0.5, 
        top_p=0.95, 
        penalty_alpha=0.6, 
        top_k=4, 
        repetition_penalty=1.03
    )
    result = tokenizer.decode(out[0])
    return result

generate("<|prompter|>What is a meme, and what's the history behind this word?<|endoftext|><|assistant|>")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/generate")
async def generateText(request: Request):
    requestJson = await request.json()
    prompt = requestJson["prompt"]
    # batch = tokenizer.encode(prompt, return_tensors="pt")    
    result = generate(prompt)
    # print(result)
    return result
