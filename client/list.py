region_of_interest = "[(333, 204), (336, 327), (520, 330), (514, 208), (333, 204)]"

roi_list = eval(region_of_interest)

x = [x[0] for x in roi_list]
y = [x[1] for x in roi_list]

print(x)
print(y)