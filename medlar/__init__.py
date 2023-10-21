# [[[fill git_describe()]]]
__version__ = '2023.10.21+parent.c437a22a'
# [[[end]]] (checksum: 0db1dd3387429d961a06754a831c4dc2)
__version_info__ = tuple(
    e if '-' not in e else e.split('-')[0] for part in __version__.split('+') for e in part.split('.') if e != 'parent'
)
