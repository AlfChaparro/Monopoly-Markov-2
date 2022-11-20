#!/usr/bin/env python
# coding: utf-8

# In[4]:


#######################################################################################################################################
# Setup
#######################################################################################################################################
import numpy as np 
import sys
import scipy.linalg as la
import pandas as pd

# For debugging
np.set_printoptions(threshold=sys.maxsize)

# States
spaceNames = ['GO','Mediterranean Ave.','Community Chest','Baltic Ave.','Income Tax','Reading Railroad','Oriental Ave.','Chance','Vermont Ave.', 'Connecticut Ave.',
                 'Jail - Just Visiting','St.Charles Place','Electric Company','States Ave.','Virginia Ave.','Pennsylvania Railroad', 'St.James Place','Community Chest','Tennessee Ave.','New York Ave.',
                'Free Parking','Kentucky Ave.','Chance','Indiana Ave.','Illinois Ave.','B&O Railroad', 'Atlantic Ave.','Ventnor Ave.','Water Works','Marvin Gardens',
                'Go To Jail','Pacific Ave.','North Carolina Ave.','Community Chest','Pennsylvania Ave.','Short Line Railroad','Chance','Park Place','Luxury Tax','Boardwalk',
                'Jail - Out in 1 turn','Jail - Out in 2 turns']

# Groups
stateGroup = ['0','1','comCard','1','0','RR','2','chCard','2','2',
             'jail','3','utility','3','3','RR','4','comCard','4','4',
             '0','5','chCard','5','5','RR','6','6','utility','6',
             ' ','7','7','comCard','7','RR','chCard','8','0','8',
             'jail','jail']
## 0: GO, free, tax
## jail, utility, RR, comCard, chCard
## 1=brown,2=teal,3=pink,4=orange,5=red,6=yellow,7=green,8=blue

# Cost, House, Hotel, Total, Rent
stateCost = ['0','60','0','60','0','200','100','0','100','120',
             '0','140','150','140','160','200','180','0','180','200',
             '0','220','0','220','240','200','260','260','150','280',
             ' ','300','300','0','320','200','0','350','0','400',
             '0','0']

stateHouse = ['0','50','0','50','0','0','50','0','50','50',
             '0','100','0','100','100','0','100','0','100','100',
             '0','150','0','150','150','0','150','150','0','150',
             ' ','200','200','0','200','0','0','200','0','200',
             '0','0']

stateHotel = ['0','50','0','50','0','0','50','0','50','50',
             '0','100','0','100','100','0','100','0','100','100',
             '0','150','0','150','150','0','150','150','0','150',
             ' ','200','200','0','200','0','0','200','0','200',
             '0','0']

stateTotal = ['0','250','0','250','0','0','250','0','250','250',
             '0','500','0','500','500','0','500','0','500','500',
             '0','750','0','750','750','0','750','750','0','750',
             ' ','1000','1000','0','1000','0','0','1000','0','1000',
             '0','0']

stateRent = ['0','250','0','450','0','0','550','0','550','600',
             '0','750','0','750','900','0','950','0','950','1000',
             '0','1050','0','1050','1100','0','1150','1150','0','1200',
             ' ','1275','1275','0','1400','0','0','1500','0','2000',
             '0','0']



# First sheet on Excel - Monopoly Data; to be appended with results.
writer = pd.ExcelWriter('Monopoly MarkovChain.xlsx', engine='xlsxwriter') #adds multiple sheets to an excel file
df_statesDefined = pd.DataFrame(spaceNames, columns=['State'])
df_statesDefined['Group'] = stateGroup
df_statesDefined['Cost'] = stateCost
df_statesDefined['House'] = stateHouse
df_statesDefined['Hotel'] = stateHotel
df_statesDefined['Total'] = stateTotal
df_statesDefined['Rent'] = stateRent
df_statesDefined.to_excel(writer, sheet_name='Monopoly Data')

#######################################################################################################################################
# Functions
#######################################################################################################################################
# Function-calculate roll probabilities of 2 dice; return [list] of %
def CalculateRollProbabilites ():
    rollProbabilities = [1,2,3,4,5,6,5,4,3,2,1]
    rollProbabilities = [x / 36 for x in rollProbabilities]
    return (rollProbabilities)

# Function-generates a matrix using two lists, a counter, and dimensions
def CreateMatrix (probabilities, matrix, counter, dim):
    if counter == dim:
        return (matrix)

    lastElement = probabilities.pop()
    probabilities = [lastElement] +probabilities
    matrix[:,counter] = probabilities
    CreateMatrix (probabilities, matrix, counter+1, dim)
    
#######################################################################################################################################    
# Roll Matrix
#######################################################################################################################################
# Create Matrix of roll probabilities
goSquareProbabilities = [0]*40 #[list] 40 board spaces
goSquareProbabilities[2:13] = CalculateRollProbabilites() #since 2 dice can only move min:2 max:13 spaces; calcs prob to land in this range in a turn
rollMatrix = np.zeros((40, 40)) #np 2D Array 40x40
rollMatrix[:,0] = goSquareProbabilities
CreateMatrix(goSquareProbabilities, rollMatrix, 1, 40) #create Matrix

# Excel sheet 2 - Roll Probability
df_goSquareProbabilities = pd.DataFrame(goSquareProbabilities, columns=['Roll Probability'])
df_goSquareProbabilities.to_excel(writer, sheet_name='Roll Probability')

# Append two columns of 0s for Jail wait 1 & Jail wait 2 states
rollMatrix = np.column_stack((rollMatrix, ([0] *40))) 
rollMatrix = np.column_stack((rollMatrix, ([0] *40)))
rollMatrix = np.row_stack((rollMatrix, ([0] *42)))
rollMatrix = np.row_stack((rollMatrix, ([0] *42)))

# Stuck in Jail (unlucky roll)
rollMatrix[40,41] = 5.0/6 # Chance of not rolling doubles; jail-out in 2 to jail-out in 1
rollMatrix[10,40] = 5.0/6 # Didn't roll double from Jail-out in 1. Next turn acts like Jail-just visiting[10] except if roll isnt double, pay fine.

# Broke Out of Jail (lucky roll)
rollMatrix[[12,14,16,18,20,22],40] = 1.0/36 #Rolled double from Jail-out in 1 (1/36=chance to land on one of 6 doubles)
rollMatrix[[12,14,16,18,20,22],41] = 1.0/36 #Rolled double from Jail-out in 2

# Excel sheet 3 - Roll-to Matrix
df_rollMatrix = pd.DataFrame(rollMatrix, index=spaceNames, columns=spaceNames)
df_rollMatrix.to_excel(writer, sheet_name=('Roll-to Matrix'))

#######################################################################################################################################
# Go to Jail Matrix
######################################################################################################################################
# Landing on Go To Jail must move to Jail space. Impossible to start turn in this space.

# Create identity matrix
goToJailRow = [1] + [0]*41 # list with 42 spaces
goToJailMatrix = np.zeros((42, 42)) #empty np 2D array 42x42 (states)
goToJailMatrix[0] = goToJailRow #combine
CreateMatrix(goToJailRow, goToJailMatrix,1,42) #creates matrix

# Send player to jail
goToJailMatrix[41,30] = 1 # Move to Jail-out in 2 turns state
goToJailMatrix[30,30] = 0 # Can't stay in GotoJail space

# Excel sheet 4 - Go To Jail Matrix
df_goToJailMatrix = pd.DataFrame(goToJailMatrix, index=spaceNames, columns=spaceNames)
df_goToJailMatrix.to_excel(writer, sheet_name='Go To Jail Matrix')

#######################################################################################################################################
# Chance Matrix
######################################################################################################################################
# 3 Chance spaces @ [7] [22] [36]
# 10/16 Chance cards move player:
## Advance to Go [0]
## Go to Jail [10]
## Go to Illinois Avenue [24]
## Go to St. Charles [11]
## Take a walk on the Boardwalk (Go to Boardwalk) [39]
## Go to Reading Railroad [5]
## Go back three spaces [if 7->4] [if 22->19] [if 36->33]
## Go to nearest Utility [if 7 or 36 -> 12] [if 22->28]
## 2 Advance to railroad [if 7->15] [if 22->25] [if 36->5]

# Create identity matrix
chanceRow = [1] + [0]*41
chanceMatrix = np.zeros((42, 42))
chanceMatrix[0] = chanceRow
CreateMatrix(chanceRow, chanceMatrix,1,42)

# Chance space 7
chanceMatrix[:,7] = [0]*42
chanceMatrix[[0,10,24,11,39,5,4,12],7] = 1.0/16
chanceMatrix[15,7] = 2.0/16 # 2 Advance to RR cards
chanceMatrix[7,7] = 6.0/16 # the other 6 cards

# Chance space 22
chanceMatrix[:,22] = [0]*42
chanceMatrix[[0,10,24,11,39,5,19,28],22] = 1.0/16
chanceMatrix[25,22] = 2.0/16
chanceMatrix[22,22] = 6.0/16

# Chance space 36
chanceMatrix[:,36] = [0]*42
chanceMatrix[[0,10,24,11,39,33,12],36] = 1.0/16
chanceMatrix[5,36] = 3.0/16
chanceMatrix[36,36] = 6.0/16

# Excel sheet 5 - Chance Card Matrix
df_chanceMatrix = pd.DataFrame(chanceMatrix, index=spaceNames, columns=spaceNames)
df_chanceMatrix.to_excel(writer, sheet_name='Chance Card Matrix')

#######################################################################################################################################
# Community Card Matrix
######################################################################################################################################
# 3 Community spaces @ [2] [17] [33]
# 2/16 Community cards move player:
## Advance to Go [0]
## Go to Jail [10]

# Create identity matrix
communityRow = [1] + [0]*41
communityMatrix = np.zeros((42, 42))
communityMatrix[0] = communityRow
CreateMatrix(communityRow, communityMatrix,1,42)


# Community space 2
communityMatrix[[0,41],2] = 1.0/16
communityMatrix[2,2] = 14.0/16 # Other cards

# Community space 17
communityMatrix[[0,41],17] = 1.0/16
communityMatrix[17,17] = 14.0/16

# Community space 33
communityMatrix[[0,41],33] = 1.0/16
communityMatrix[33,33] = 14.0/16

# Excel sheet 5 - Community Card Matrix
df_communityMatrix = pd.DataFrame(communityMatrix, index=spaceNames, columns=spaceNames)
df_communityMatrix.to_excel(writer, sheet_name='Community Card Matrix')

#######################################################################################################################################
# Three Doubles To Jail Matrix
######################################################################################################################################
# Create Identity Matrix except 215/216 instead of 1 (prob. of not getting 3 doubles in a row, thus no jail)
threeDoublesJailRow = [215.0/216] + [0]*41 # 215/216 = 0.99537
threeDoublesJailMatrix = np.zeros((42, 42))
threeDoublesJailMatrix[0] = threeDoublesJailRow
CreateMatrix(threeDoublesJailRow, threeDoublesJailMatrix,1,42)

# Prob. of rolling doubles 3 times from any state except jail
threeDoublesJailMatrix[41,[range(0,40)]]=1.0/216 #Jail-out in 2
threeDoublesJailMatrix[30,30]=0 # Cannot end turn in Go To Jail space
threeDoublesJailMatrix[41,30]=1 # Move to jail no matter what
threeDoublesJailMatrix[41,41]=1 # Already in jail
threeDoublesJailMatrix[40,40]=1 # Already in jail

# Excel sheet 6 - Three Doubles To Jail Matrix
df_threeDoublesJailMatrix = pd.DataFrame(threeDoublesJailMatrix, index=spaceNames, columns=spaceNames)
df_threeDoublesJailMatrix.to_excel(writer, sheet_name='Three Doubles To Jail Matrix')

#######################################################################################################################################
# Final Matrix
######################################################################################################################################
# Final Transition Matrix = community x chance x gotoJail x roll x 3dlbsJail
finalMatrix = np.matmul(np.matmul(np.matmul(np.matmul(communityMatrix, chanceMatrix), goToJailMatrix), rollMatrix), threeDoublesJailMatrix)

# Excel sheet 7 - Final Transition Matrix
df_finalMatrix = pd.DataFrame(finalMatrix, index=spaceNames, columns=spaceNames)
df_finalMatrix.to_excel(writer, sheet_name='Final Transition Matrix')

# Option1: Multiply matrix thousands of times (too much computational power)
# Option2: Retrieve EigenVector from finalMatrix to get steady state vector (frequencies of each state)
eigenVector = la.eig(finalMatrix)[1]
steadyStateVec = eigenVector[:,0]
steadyStateVec = steadyStateVec/sum(steadyStateVec)

# Append final probability to Excel sheet 1 - Monopoly Data
df_statesDefined['Probability Results'] = steadyStateVec
df_statesDefined.to_excel(writer, sheet_name='Monopoly Data')

# Save sheets to Excel file for download
writer.save()

