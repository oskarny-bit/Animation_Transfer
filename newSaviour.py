from maya import OpenMayaUI as omui
import PySide2
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtUiTools import *
from PySide2.QtWidgets import *
from shiboken2 import wrapInstance

import pymel.core as pm
import pymel.core.datatypes as dt

nameOfSourceRootJoint = "SourceRootJoint"
nameOfTargetRootJoint = "TargetRootJoint"
rootJointNodeSource = 1
rootJointNodeTarget = 1
listOfJointSource = []
listOfJointTarget = []
totalKeyframes = 40

rootBindPoseOrientation = 1
sBindPose = []
tBindPose = []
sParentBPOri = []
tParentBPOri = []

sJointRot = []
sJointOri = []
tJointOri = []
finalRot = []

##########################################################################################

def populateSkeleList(rootNode, skeleList):
    skeleList.append(rootNode)
    for element in rootNode.getChildren():
        if element.numChildren() > 0:
            populateSkeleList(element, skeleList)
    return skeleList
        
def printRootJointNode(rootJoin, nameOfRootJoint):
    rootJoin = pm.nodetypes.Joint(nameOfRootJoint)
    return rootJoin

def addItemToQWList(qwList, jointList):
    qwList.clear()
    #print jointList
    for element in jointList:
        qwList.addItem(str(element))

def getRotInfo(jointRot, skeleList):
    for ele in skeleList:
        jointRot.append(ele.getRotation().asMatrix())

def getOriInfo(jointOri, skeleList):
    for ele in skeleList:
        jointOri.append(ele.getOrientation().asMatrix())

def getParents(bone):
    parentMatrix = []
    parentJoint = bone.getParent()
    if type(parentJoint) == pm.nodetypes.Joint:
        parentMatrix = getParents(parentJoint)
    else:
        return listOfJointSource[0].getRotation().asMatrix() * listOfJointSource[0].getOrientation().asMatrix()
    return (parentJoint.getRotation().asMatrix() * parentJoint.getOrientation().asMatrix()) * parentMatrix

def bindPoseInfo(bindPose, parentBindPoseOri, skeleList, rootBPO):
    for ele in skeleList:
        bindPose.append(ele.getRotation().asMatrix())
        
        if ele == skeleList[0]:
            parentBindPoseOri.append(rootBPO)
        else:
            parentBindPoseOri.append(getParents(ele))
                   
##########################################################################################

def getMayaWin():
	mayaWinPtr = omui.MQtUtil.mainWindow( )
	mayaWin = wrapInstance( long( mayaWinPtr ), QWidget )

def loadUI( path ):
	loader = QUiLoader()
	uiFile = QFile( path )

	dirIconShapes = ""
	buff = None

	if uiFile.exists():
		dirIconShapes = path
		uiFile.open( QFile.ReadOnly )

		buff = QByteArray( uiFile.readAll() )
		uiFile.close()
	else:
		print "UI file missing! Exiting..."
		exit(-1)

	fixXML( path, buff )
	qbuff = QBuffer()
	qbuff.open( QBuffer.ReadOnly | QBuffer.WriteOnly )
	qbuff.write( buff )
	qbuff.seek( 0 )
	ui = loader.load( qbuff, parentWidget = getMayaWin() )
	ui.path = path

	return ui


def fixXML( path, qbyteArray ):
	# first replace forward slashes for backslashes
	if path[-1] != '/':
		path += '/'
	path = path.replace( "/", "\\" )

	# construct whole new path with <pixmap> at the begining
	tempArr = QByteArray( "<pixmap>" + path + "\\" )

	# search for the word <pixmap>
	lastPos = qbyteArray.indexOf( "<pixmap>", 0 )
	while lastPos != -1:
		qbyteArray.replace( lastPos, len( "<pixmap>" ), tempArr )
		lastPos = qbyteArray.indexOf( "<pixmap>", lastPos + 1 )
	return


class UIController:
	def __init__( self, ui ):
	
		# Connect each signal to it's slot one by one
		ui.SJ_Load.clicked.connect( self.ButtonClicked )
		ui.SJ_Delete.clicked.connect( self.DeleteClicked )
		ui.SJ_Up.clicked.connect( self.UpClicked )
		ui.SJ_Down.clicked.connect( self.DownClicked )
		ui.SJ_Refresh.clicked.connect( self.Refresh )
		ui.TJ_Load.clicked.connect( self.TargetAddButton )
		ui.TJ_Refresh.clicked.connect( self.TargetRefresh )
		ui.TJ_Delete.clicked.connect( self.TargetDelete )
		ui.TJ_Up.clicked.connect( self.TargetUp )
		ui.TJ_Down.clicked.connect( self.TargetDown )
		ui.AniTransfer.clicked.connect(self.AnimationTransfer)

		self.ui = ui
		ui.setWindowFlags( Qt.WindowStaysOnTopHint )
		ui.show()
        
	def ButtonClicked( self ):
		global nameOfSourceRootJoint
		global rootJointNodeSource
		global listOfJointSource
		global rootBindPoseOrientation

		self.ui.SJ_Text.selectAll()
		nameOfSourceRootJoint = self.ui.SJ_Text.text()
		rootJointNodeSource = printRootJointNode(rootJointNodeSource, nameOfSourceRootJoint)
		listOfJointSource = populateSkeleList(rootJointNodeSource, listOfJointSource)
		addItemToQWList(self.ui.SJ_List, listOfJointSource)
		
		# secures the bind poses of all joints along with the parent's bind pose for each joint...
	        # important that both skeletons have the same bind pose in world space as the... 
	            # bind pose plays a vital part in the matrix calculations.
		rootBindPoseOrientation = listOfJointSource[0].getOrientation().asMatrix()
		pm.currentTime(0)
		# pre-calculate the bind pose because this will be constant
		bindPoseInfo(sBindPose, sParentBPOri, listOfJointSource, rootBindPoseOrientation)
		
	def TargetAddButton ( self ):
	    global nameOfTargetRootJoint
	    global rootJointNodeTarget
	    global listOfJointTarget
	    global rootBindPoseOrientation
	    
	    self.ui.TJ_Text.selectAll()
	    nameOfTargetRootJoint = self.ui.TJ_Text.text()
	    rootJointNodeTarget = printRootJointNode(rootJointNodeTarget, nameOfTargetRootJoint)
	    listOfJointTarget = populateSkeleList(rootJointNodeTarget, listOfJointTarget)
	    addItemToQWList(self.ui.TJ_List, listOfJointTarget)
	    
	    # secures the bind poses of all joints along with the parent's bind pose for each joint...
	        # important that both skeletons have the same bind pose in world space as the... 
	            # bind pose plays a vital part in the matrix calculations.
	    pm.currentTime(0)
	    pm.setKeyframe(listOfJointTarget)
	    # pre-calculate the bind pose because this will be constant
	    bindPoseInfo(tBindPose, tParentBPOri, listOfJointTarget, rootBindPoseOrientation)
        
	def DeleteClicked( self ):
	    index = self.ui.SJ_List.currentIndex()
	    del listOfJointSource[index.row()]
	    print listOfJointSource
	    addItemToQWList(self.ui.SJ_List, listOfJointSource)
	    
	def TargetDelete( self ):
	    index = self.ui.TJ_List.currentIndex()
	    del listOfJointTarget[index.row()]
	    print listOfJointTarget
	    addItemToQWList(self.ui.TJ_List, listOfJointTarget)
        
	def UpClicked( self ):
	    index = self.ui.SJ_List.currentIndex()
	    temp = listOfJointSource[index.row()-1]
	    listOfJointSource[index.row()-1] = listOfJointSource[index.row()]
	    listOfJointSource[index.row()] = temp
	    print listOfJointSource
	    addItemToQWList(self.ui.SJ_List, listOfJointSource)
	      
	def TargetUp( self ):
	    index = self.ui.TJ_List.currentIndex()
	    temp = listOfJointTarget[index.row()-1]
	    listOfJointTarget[index.row()-1] = listOfJointTarget[index.row()]
	    listOfJointTarget[index.row()] = temp
	    print listOfJointTarget
	    addItemToQWList(self.ui.TJ_List, listOfJointTarget)
	
	def DownClicked( self ):
	    index = self.ui.SJ_List.currentIndex()
	    temp = listOfJointSource[index.row()+1]
	    listOfJointSource[index.row()+1] = listOfJointSource[index.row()]
	    listOfJointSource[index.row()] = temp
	    print listOfJointSource
	    addItemToQWList(self.ui.SJ_List, listOfJointSource)
	    
	def TargetDown( self ):
	    index = self.ui.TJ_List.currentIndex()
	    temp = listOfJointTarget[index.row()+1]
	    listOfJointTarget[index.row()+1] = listOfJointTarget[index.row()]
	    listOfJointTarget[index.row()] = temp
	    print listOfJointTarget
	    addItemToQWList(self.ui.TJ_List, listOfJointTarget)
	
	def Refresh(self):
	    global listOfJointSource
	    global rootBindPoseOrientation

	    del sBindPose[:]
	    del sParentBPOri[:]
	    
	    bindPoseInfo(sBindPose, sParentBPOri, listOfJointSource, rootBindPoseOrientation)
	
	def TargetRefresh( self ):
	    global listOfJointTarget
	    global rootBindPoseOrientation
	    
	    del tBindPose[:]
	    del tParentBPOri[:]
	    
	    pm.setKeyframe(listOfJointTarget)
	    bindPoseInfo(tBindPose, tParentBPOri, listOfJointTarget, rootBindPoseOrientation)
	
	def AnimationTransfer( self ):
	    # skip "index"(key) 0 as this is the bind pose which we've already stored        
	    for key in range(1, totalKeyframes):
	        pm.currentTime(key)
	        del sJointRot[:]
	        del sJointOri[:]
	        del tJointOri[:]
	        del finalRot[:]
	        
	        listOfJointTarget[0].setTranslation(listOfJointSource[0].getTranslation())
	        getRotInfo(sJointRot, listOfJointSource)
	        getOriInfo(sJointOri, listOfJointSource)
	        getOriInfo(tJointOri, listOfJointTarget)
	        
	        for x in range(len(listOfJointSource)):
	            # model space - e.g. the inverse takes us from bind pose to origo 
	            isolatedRot = sBindPose[x].inverse() * sJointRot[x]
	            # world space 
	            worldRot = sJointOri[x].inverse() * sParentBPOri[x].inverse() * isolatedRot * sParentBPOri[x] * sJointOri[x]
	            # target space 
	            targetRot = tJointOri[x] * tParentBPOri[x] * worldRot * tParentBPOri[x].inverse() * tJointOri[x].inverse()
	            
	            # set root rot of target to be the same as source
	            if x == 0:
	                finalRot.append(sJointRot[0])
	            else:
	                finalRot.append(tBindPose[x] * targetRot)
	        
	        # set the change of base rotation for each target-joint
	        for y in range(len(listOfJointSource)):
	            listOfJointTarget[y].setRotation(dt.degrees(dt.EulerRotation(finalRot[y])))
	        pm.setKeyframe(listOfJointTarget)