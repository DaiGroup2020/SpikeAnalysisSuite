# SpikeAnalysisClient

Spike-analysis software using a client/server architecture.


## Requirements

Create a virtual environment and install the Python dependencies with:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Local configuration

Set SPIKE_SERVER_HOST to your server address (default: 127.0.0.1). Use an opaque account alias for login. The optional saved-login file contains credentials; it is excluded from Git.

Local processing uses ~/Documents/SpikeAnalysisCache/ as disposable scratch space. Keep permanent data outside that directory.

Install the external sorting tools required by your workflow before launching the Python entry point. Run only on a trusted network; this publication cleanup does not add transport encryption or redesign authentication.

Version 1 contributor: Jinyu Zang
