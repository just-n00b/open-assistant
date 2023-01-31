import torch
from torch import nn
from torch.nn import functional as F
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import StoppingCriteria, StoppingCriteriaList
from fastapi import Request, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from types import SimpleNamespace

base_path = 'Rallio67/chip_20B_instruct_alpha'
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


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/generate")
async def generateText(request: Request):
    params = SimpleNamespace()
    params.stopWords = ["\n\n\n"]
    requestJson = await request.json()
    stop_words = params.stopWords
    stop_ids = [tokenizer.encode(w)[0] for w in stop_words]
    stop_criteria = KeywordsStoppingCriteria(stop_ids)
    prompt = requestJson["prompt"]
    # batch = tokenizer.encode(prompt, return_tensors="pt")
    encoded_input = tokenizer(prompt, return_tensors='pt')
    out = model.generate(
        input_ids=encoded_input['input_ids'].cuda(0),
        do_sample=True,
        num_beams=1,
        use_cache=False,
        eos_token_id=0,
        pad_token_id=0,
        max_new_tokens=1,
        num_return_sequences=1,
        # stopping_criteria=StoppingCriteriaList([stop_criteria]),
        temperature=0.6, 
        top_p=0.95, 
        penalty_alpha=0.6, 
        top_k=4, 
        repetition_penalty=1.03
    )
    result = tokenizer.decode(out[0])
    # print(result)
    return result
