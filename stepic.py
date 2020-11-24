n = int(input())
space = {'global': []}


def create(nsp, arg):
    space[nsp] = []
    space[arg].append(nsp)


def add(nsp, arg):
    space[nsp].append(arg)


def get(nsp, arg):
    x = space.get(nsp)
    if x == 'None':
        return x
    if arg in x:
        return nsp
    else:
        for i in space.keys():
            if nsp in space[i]:
                return get(i, arg)


response = []
for i in range(n):
    cmd, nsp, arg = input().split()
    if cmd == 'create':
        create(nsp, arg)
    elif cmd == 'add':
        add(nsp, arg)
    elif cmd == 'get':
        response.append(get(nsp, arg))
for i in response:
    print(i)
