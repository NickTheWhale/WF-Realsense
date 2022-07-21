
# Python program to flatten a nested list
 
# explicit function to flatten a
# nested list
class DummyClass():
    def __init__(self):
        dummy_var = None



def flattenList(nestedList):
 
    # check if list is empty
    if not(bool(nestedList)):
        return nestedList
 
     # to check instance of list is empty or not
    if isinstance(nestedList[0], list):
 
        # call function with sublist as argument
        return flattenList(*nestedList[:1]) + flattenList(nestedList[1:])
 
    # call function with sublist as argument
    return nestedList[:1] + flattenList(nestedList[1:])
 
 
# Driver Code

obj = DummyClass()

nestedList = [1, 2, 3, 4, [2, 3, 4, 5, [obj, 4, 5, 6]], [3, 4, 5, 5]]
print('Nested List:\n', nestedList)
 
print("Flattened List:\n", flattenList(nestedList))