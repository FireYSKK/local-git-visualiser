import binascii
import zlib
import graphviz


def read_git_object(git_file: str):
    folder = git_file[:2]
    name = git_file[2:]

    filename = f"test/.git/objects/{folder}/{name}"

    with open(filename, "rb") as file:
        raw_data = file.read()
    data = zlib.decompress(raw_data)

    _type, contents = data.split(b'\x00', maxsplit=1)[0:2]
    _type = _type.decode().split()[0]
    _contents = None
    if _type in ["blob", "commit"]:
        _contents = contents.decode()
    elif _type == "tree":
        _contents = list()
        while contents != b'':
            filemode, contents = contents.split(b' ', maxsplit=1)
            filename, contents = contents.split(b'\x00', maxsplit=1)
            sha1, contents = contents[:20], contents[20:]
            filemode = filemode.decode()
            filename = filename.decode()
            sha1 = binascii.hexlify(sha1).decode()
            _contents.append((filemode, filename, sha1))
    return _type, _contents


def read_heads(heads_name: str):
    filename = f"test/.git/refs/heads/{heads_name}"

    with open(filename, "rb") as file:
        data = file.read()
    contents = data.split(b'\x00', maxsplit=1)[0].decode()

    return contents


dot = graphviz.Digraph("git rep")
for heads_file in ['master']:
    content = read_git_object(read_heads(heads_file)[:-1])
    dot.node(content[1].split('\n')[-2])

    tree = None
    tree_short_name = "empty"
    parent_name = content[1].split('\n')[-2]
    if content[0] == 'commit':
        content_split = content[1].split(maxsplit=1)
        if content_split[0] == 'tree':
            tree = read_git_object(content_split[1].split('\n', maxsplit=1)[0])
            tree_short_name = content_split[1][:6]

    while (tree) and tree[0] == 'tree':
        dot.node('Tree '+ tree_short_name)
        dot.edge(parent_name, 'Tree ' + tree_short_name)

        next_tree = None
        for child in tree[1]:
            if child[0] == '40000':
                next_tree = read_git_object(child[2])
                next_tree_short_name = child[2][:6]
            elif child[0] == '100644':
                dot.node(child[1])
                dot.edge('Tree ' + tree_short_name, child[1])
        tree = next_tree
        parent_name = 'Tree ' + tree_short_name
        tree_short_name = next_tree_short_name

print(dot.source)