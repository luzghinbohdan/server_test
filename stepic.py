dict_par = {'global':'None'}
dict_var = {'global':[]}
def create(namespace,arg):
    global dict_par,dict_var
    dict_par[namespace]=arg
    dict_var[namespace]=[]
def add(namespace,arg):
    global dict_var
    dict_var[namespace].append(arg)
def get(namespace,arg):
    global dict_par,dict_var

amount=int(input())
response=[]
for i in range(amount):
    cmd,namespace,arg=input().split()
    if cmd == 'create':
        create(namespace,arg)
    if cmd == 'add':
        add(namespace,arg)
    if cmd == 'get':
        response.append(get(namespace,arg))
print(dict_var,dict_par)
for i in response:
    print(i)