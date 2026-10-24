# SpikeAnalysisSuite

Client-server software for neural spike recording, sorting, curation, and analysis.

## Repository structure

- `SpikeAnalysisClient/`: desktop client and user interface.
- `SpikeAnalysisServer/`: server-side task management and processing services.

## Requirements

Both components are Python applications. Install their dependencies separately:

```bash
python -m pip install -r SpikeAnalysisClient/requirements.txt
python -m pip install -r SpikeAnalysisServer/requirements.txt
```

The workflow also requires the external spike-sorting tools used by your analysis pipeline, such as Kilosort and Phy. See the component READMEs for configuration details.

## Configuration

The client uses `SPIKE_SERVER_HOST` to locate the server and defaults to `127.0.0.1`.

The server uses `SPIKE_DATA_ROOT` for recording data and optional `KILOSORT_PATH`, `KILOSORT2_PATH`, and `KILOSORT3_PATH` variables for local sorter installations. Copy `SpikeAnalysisServer/GUI_support/settings/user_info_data.example.json` to the ignored `user_info_data.json` file and replace the example password before use.

Do not commit real credentials, experimental data, or local machine configuration files.

## Version 1

This repository archives Version 1 of the SpikeAnalysisSuite. The original Version 1 contributor is Jinyu Zang.

## License

Add the license selected by the Automorphism2023 research group before distributing derivative versions.
