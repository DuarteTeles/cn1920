Under `scripts/` are all the scripts used to obtain the reported results:

- `parse-arxiv-xml.py` is used to transform from the xml representation to a format readable by networkx. The script outputs to stdout, so you should make sure to pipe the output to a file called `arxiv.network-compatible`.
- `graph-information.ipynb` reads the above file and outputs some statistics about the graph, as well as writing the graph's degree distribution into a file called `degree-dist.data`.
- `degree-frequency-plotter.ipynb` reads the above file, plots the degree distribution and tries to fit an $ak^{-\gamma}$ function to the data, where $a$ is supplied by the user to correct where the resulting curve starts. $\gamma$ should be calculated using the [`plfit`](https://github.com/ntamas/plfit) library.

The data used is available under `data/`. `arXiv_physics_2018-07-04.xml.tar.bz2` and `arXiv_physics_astro-ph_2018-07-04.xml.tar.bz2` had to be split to be kept under Github's maximum file size limit. To reconstruct the archives, you can simply `cat` the files together.
