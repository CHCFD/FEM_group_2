# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 04:35:48 2020
JP something meaningful
@author: chanc
haha
I have spyder
I love spyder 
I dont like it. It's not a chat program!!
@author: chanc, JP something  meaningful,
"""
import math
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint

N_el = 5 # No. of elements
N_nodes = N_el + 1
Lx = 4
left = 0 - Lx/2
right = 0 + Lx/2
lamda = 0.
x_nodes = np.linspace(left,right,N_nodes)
y_nodes = np.linspace(0,0,N_nodes)
dx = Lx/N_el
gD = 200. # Dirichlet boundary condition  
 
def shape(N_loc, N_gi):
    """ Define Reference shape functions - their values at N_gi quadrature points.
    
    Only implemented for N_loc = 2, i.e two nodes per element - linear basis functions.
    """
    assert(N_loc==2)
    phi = np.zeros((N_loc, N_gi))
    if(N_gi ==2):
        phi[0,0] = 1.0
        phi[0,1] = 0.0
        phi[1,0] = 0.0
        phi[1,1] = 1.0
    elif(N_gi ==3):
        phi[0,0] = 1.0
        phi[0,1] = 0.5
        phi[0,2] = 0.0
        phi[1,0] = 0.0
        phi[1,1] = 0.5
        phi[1,2] = 1.0
    else:
        raise Exception('N_gi value not implemented')
    return phi

def shape_deriv(dx, N_loc, N_gi):
    """ Define derivatives of shape functions - their values of N_gi quadrature points
    over the reference element.
    
    Only implemented for N_loc = 2, i.e. two nodes per element - 
    linear basis functions.
    """
    
    assert(N_loc == 2)
    phi_x = np.zeros((N_loc, N_gi))
    if(N_gi==2):
        phi_x[0,0] = -1./2.
        phi_x[0,1] = phi_x[0,0]
        phi_x[1,0] = -phi_x[0,0]
        phi_x[1,1] = phi_x[1,0]
    elif(N_gi==3):
        phi_x[0,0] = -1./2.
        phi_x[0,1] = phi_x[0,0]
        phi_x[0,2] = phi_x[0,0]
        phi_x[1,0] = -phi_x[0,0]
        phi_x[1,1] = phi_x[1,0]
        phi_x[1,2] = phi_x[1,0]
    else:
        raise Exception('N_gi value not implemented')
    # Jacobian contribution as seen/explained above due to the user of the chain rule
    phi_x = phi_x *(2./dx)
    return phi_x

def quadrature(N_gi):
    """ Define quadrature rule on N_gi quadrature points.
    """
    weight = np.zeros(N_gi)
    if(N_gi==2):
        weight[0] = 0.5
        weight[1] = 0.5
    elif(N_gi==3):
        weight[0] = 1./3
        weight[1] = 4./3
        weight[2] = 1./3
    else:
        raise Exception('N_gi value not implemented')
    return weight

def connectivity(N_loc, N_elements_CG):
    """ Generate the connectivity matrix of dimension N_loc * N_elements_CG.
    
    Row corresponds to the local node number, column to the element number,
    the entry of the matrix is then a global node number.
    
    Returns: Connectivity matrix
    """
    connectivity_matrix = np.zeros((N_loc, N_elements_CG), dtype =int)
    if(N_loc==2):
        for element in range(N_elements_CG):
            connectivity_matrix[0, element] = element
            connectivity_matrix[1, element] = element + 1
    else:
        raise Exception('Only linear elements (N_loc= 2) implemented.')
    return connectivity_matrix

# Compute the local Mass and Laplace Matrix
N_gi = 3    # Define Quadrature Points
N_loc = 2   # 2 Nodes per element
weight  = quadrature(N_gi)
phi = shape(N_loc, N_gi)
phi_x = shape_deriv(dx, N_loc, N_gi)

MElem = np.zeros((N_loc,N_loc))
LElem = np.zeros((N_loc,N_loc))

for i_loc in range(N_loc):
    for j_loc in range(N_loc):
        for gi in range(N_gi):
            MElem[i_loc, j_loc] += weight[gi] * phi[i_loc,gi] * phi[j_loc, gi] * dx/2. #dx/2 here is the Jacobian determinant
            LElem[i_loc, j_loc] += weight[gi] * phi_x[i_loc, gi] * phi_x[j_loc, gi] * dx/2.
print("Local Mass Matrix")
print(MElem)
print("Local Laplacian Matrix")
print(LElem)


def assembly(LocalMatrix, connectivity_matrix, N_elements):
    """ Perform local assembly by looping over the glocal co-ordinates and
    adding contributions to the correct locations of the global discretization matrices.
    """
    
    GlobalMatrix = np.zeros((N_elements+1,N_elements+1))
    for element in range(N_elements):
        for i_loc in range(N_loc):
            i_global = connectivity_matrix[i_loc, element]
            for j_loc in range(N_loc):
                j_global = connectivity_matrix[j_loc, element]
                GlobalMatrix[i_global, j_global] = GlobalMatrix[i_global, j_global] + LocalMatrix[i_loc,j_loc]
    return GlobalMatrix

# Assembly Matrix for global Mass and Laplacian
connectivity_matrix = connectivity(N_loc, N_el)
MG = assembly(MElem,connectivity_matrix,N_el)
LG = assembly(LElem,connectivity_matrix,N_el)
Stiff = LG + lamda*MG

# RHS of Matrix
def f(x):
    return 100.0*math.exp(x)

Fsource = np.zeros(N_nodes)

# loop over elements
for element in range(N_el):
    # loop ocver local nodes (i: test functions)
    for i_local in range(N_loc):
        i_global = connectivity_matrix[i_local, element]
        for gi in range(N_gi):
            Fsource[i_global] += weight[gi]*phi[i_loc,gi]*f(x_nodes[i_global]+gi*dx/2.) *dx/2.

def apply_bcs(A, b, lbc, rbc, bc_option=0):
    """ Apply BCs using big spring method.
    
    bc_option==0 Homogeneous Neumann
    bc_option==1 Dirichlet
    """
    
    if(bc_option==0):
        return
    elif(bc_option==1):
        big_spring = 1.0e10
        A[0,0] = big_spring
        b[0] = big_spring *lbc
        A[-1,-1] = big_spring
        b[-1] = big_spring*rbc
    else:
        raise Exception('bc option not implemented')

# Solving
RHS = -Fsource
apply_bcs(Stiff,RHS,0,0,1)
uH = np.linalg.inv(Stiff)@Fsource
# Adding Dirichlet BCs
u = uH + gD


# Plotting
plt.plot(x_nodes,u, '-o')
plt.grid()
plt.xlabel('x')
plt.ylabel('T')
plt.title('Temperature Distribution for L='+str(Lx)+'    $N_{el}=$'+str(N_el))


