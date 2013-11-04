from copy import copy, deepcopy

def perms(s):
    n = len(s)
    if n <= 1:
        return [s]
    else:
        result = []
        for ind in range(n):
            outside = s[ind]
            inside = deepcopy(s)
            del inside[ind]

            subperms = perms(inside)
            for pp in subperms:
                pp.insert(0, outside)
            result.extend(subperms)
        return result

def combs(s):
    n = len(s)
    if n <= 1:
        return [s]
    else:
        result = [[s[0]]]
        subcombs = combs(s[1:])

        result.extend(deepcopy(subcombs))

        for cc in subcombs:
            cc.insert(0, s[0])
        result.extend(subcombs)
    return result

def main():
    p = perms(['x','y','z'])
    print len(p), "\n-----\n", "\n".join(["".join([str(ppp) for ppp in pp]) for pp in p]), '\n'
    p = combs(['w','x','y','z'])
    print len(p), "\n-----\n", "\n".join(["".join([str(ppp) for ppp in pp]) for pp in p]), '\n'

if __name__ == "__main__":
    main()
