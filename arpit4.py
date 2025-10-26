def minDigit(num):
    s=9
    while num:
        l=num%10
        if s>l:
            s=l
        num//=10
    return s
def maxDigit(num):
    m=0
    while num:
        l=num%10
        if m<l:
            m=l
        num//=10

    return m
T=int(input())
for i in range (T):
    num=int(input())
    print(minDigit(num), maxDigit(num))
