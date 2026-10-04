
import networkx as nx
import sys
import math

def distancia(node1,node2):
	"""Returns the euclidean distance between two nodes"""
	n1 = getCoordinates(node1)
	n2 = getCoordinates(node2)
	d = math.sqrt(math.pow(n2[0]-n1[0],2)+math.pow(n2[1]-n1[1],2))
	return d

def getCoordinates(nodeId):
	"""calculates the coordinates of an node id according to the grid used by the simulation """
	x = (nodeId-1)%50
	y = (nodeId-1)//50
	coord = [x,y]
	return coord

#este programa recibe como parametro un grafo en formato adjlist y un factor que puede ser 1,2,4,8,16, el cual indica el tam maximo de enlace
factor=sys.argv[2]
tamEnlace=math.sqrt(math.pow(49,2)+math.pow(49,2))/int(factor)
G = nx.read_adjlist(sys.argv[1], nodetype=int)
distancias=[]
for i in G.edges():
	distancias.append(distancia(i[0],i[1]))
print(sorted(distancias))
print(len(distancias))
indiceMaximo=distancias.index(max(distancias))
print("maxima distancia posible",tamEnlace)
print("la distancia mas grande en el grafo es",distancias[indiceMaximo],"esta se da entre",list(G.edges())[indiceMaximo])