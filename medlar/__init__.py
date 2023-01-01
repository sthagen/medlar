# [[[fill git_describe()]]]
__version__ = '2022.11.28+parent.63423cd2'
# [[[end]]] (checksum: d6cbb972a54f39fd72aca87bc1189801)
__version_info__ = tuple(
    e if '-' not in e else e.split('-')[0] for part in __version__.split('+') for e in part.split('.') if e != 'parent'
)
