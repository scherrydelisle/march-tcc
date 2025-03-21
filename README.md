# Getting started

```bash 
# create virtual env
python -m venv myenv
source myenv/bin/activate

# install dependencies
pip install --upgrade pip
pip install -r reqs.txt jupyterlab
```

Now you can start the jupyter lab by: `jupyter lab`

# Tutorial Notebooks

This repository contains a series of Jupyter notebooks that demonstrate various AI techniques using Claude models from Anthropic. Below is a table highlighting what each notebook covers:

| Notebook | Description |
|----------|-------------|
| [0_intro.ipynb](0_intro.ipynb) | Environment setup check |
| [1_prompt.ipynb](1_prompt.ipynb) | Prompt engineering basics |
| [2_simple_rag.ipynb](2_simple_rag.ipynb) | Retrieval-augmented generation |
| [3_tools.ipynb](3_tools.ipynb) | Tool usage implementation |
| [4_workflow.ipynb](4_workflow.ipynb) | Multi-step LLM chains |
| [5_agent_simple.ipynb](5_agent_simple.ipynb) | Car rental agent |

We also have, 
- `workflow_irl.py` for realistic workflow example. 
- `docs/example.txt` for example dataset for rag
- `docs/2024ltr.pdf` for example dataset for rag
- `docs/car_rental_faq.md` for example dataset for simple agent! 


