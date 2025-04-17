site-packages/attrdict/mapping.pt, merge.py, mixins.py, default.py:
Change every occurence of
	from collections import Mapping
to
	from collections.abc import Mapping

site-packages/e2cnn/kernels/utils.py:
Change every occurence of
	np.array(obj, copy=False)
to
	np.asarray(obj)
obj is probably something like k, s, or gamma.

