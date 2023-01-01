# [[[fill git_describe()]]]
__version__ = '2023.1.1+parent.1e7e582d'
# [[[end]]] (checksum: 4a8833329674c89a7222cf390f7e21b8)
__version_info__ = tuple(
    e if '-' not in e else e.split('-')[0] for part in __version__.split('+') for e in part.split('.') if e != 'parent'
)
