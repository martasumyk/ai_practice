# Computer Use Agent (UI-TARS, open source)

[Paper link](https://arxiv.org/abs/2501.12326)


## Intro

UI-TARS-1.5, an open-source multimodal agent built upon a powerful vision-language model (Qwen).


## Setup

Install:

```
pip install ui-tars
```

Create an endpoint on HuggingFace ([instruction](https://github.com/bytedance/UI-TARS/blob/main/README_deploy.md))

Create `.env` file, pass the model name as well as HF_TOKEN and HF_BASE_URL.

```
MODEL_ID=ByteDance-Seed/UI-TARS-1.5-7B
```

Run main:

```
python computer-use-agents/ui-tars/main.py
```


Also, you can try to change task and prompt in the `config.py` file.

