from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from MainWindow import Ui_MainWindow
import MainWindow
import sys



class Ui_MainWindow(Ui_MainWindow):
    def add_random_creature_event(self):
        pass
    def heal_event(self):
        pass
    def kill_event(self):
        pass
    def reproduce_event(self):
        pass
    def copy_event(self):
        pass
    def paste_event(self):
        pass
    def disperse_cells_event(self):
        pass

    def setupUi(self, MainWindow):
        super(Ui_MainWindow, self).setupUi(MainWindow)
        self.worldView = World_View(self.centralwidget)
        self.worldView.setGeometry(QtCore.QRect(15, 20, 1070, 600))
        self.worldView.setObjectName("worldView")

        self.worldView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.worldView.customContextMenuRequested[QtCore.QPoint].connect(self.rightMenuShow)

        self.scene = QtWidgets.QGraphicsScene(self.worldView)
        self.scene.setSceneRect(0, 0, 3000, 1800)
        self.worldView.setScene(self.scene)

        self.worldView.fitInView()

        self.worldView.setBackgroundBrush( QtGui.QBrush( QtGui.QColor(180,180,255) ) )



class World_View(QtWidgets.QGraphicsView):
    _zoom = 0

    def __init__(self, cWidget):
        super(World_View, self).__init__(cWidget)
        self.setBackgroundBrush( QtGui.QBrush( QtGui.QColor(180,180,255) ) )

    def wheelEvent(self, event):
        self._zoom
        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1
        if self._zoom > 0:
            self.scale(factor, factor)
        elif self._zoom == 0:
            self.fitInView()
        else:
            self._zoom = 0

    def updateView(self):
        scene = self.scene()
        r = scene.sceneRect()
        self.fitInView()

    def showEvent(self, event):
        if not event.spontaneous():
            self.updateView()

    def fitInView(self, scale=False):
        rect = QtCore.QRectF(self.scene().sceneRect())
        if not rect.isNull():
            self.setSceneRect(rect)
            unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
            self.scale(1 / unity.width(), 1 / unity.height())
            viewrect = self.viewport().rect()
            scenerect = self.transform().mapRect(rect)
            factor = min(viewrect.width() / scenerect.width(),
                         viewrect.height() / scenerect.height())
            self.scale(factor, factor)
            self._zoom = 0

    def mousePressEvent(self, event):
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        super(World_View, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        super(World_View, self).mouseReleaseEvent(event)



def rightMenuShow(self):
    pos = QtGui.QCursor.pos()
    print("Pos: {}".format(pos))
    #rightMenu = QtWidgets.QMenu(self.listView1)
    rightMenu = QtWidgets.QMenu()

    addAction = QtWidgets.QAction(u"Add Random Organism", triggered=self.add_random_creature_event)
    healAction = QtWidgets.QAction(u"Heal", triggered=self.heal_event)
    killAction = QtWidgets.QAction(u"Kill", triggered=self.kill_event)
    reproduceAction = QtWidgets.QAction(u"Reproduce", triggered=self.reproduce_event)
    copyAction = QtWidgets.QAction(u"Copy", triggered=self.copy_event)
    pasteAction = QtWidgets.QAction(u"Paste", triggered=self.paste_event)
    disperseCellsAction = QtWidgets.QAction(u"Disperse All Dead Cells", triggered=self.disperse_cells_event)
    rightMenu.addAction(addAction)
    rightMenu.addAction(healAction)
    rightMenu.addAction(killAction)
    rightMenu.addAction(reproduceAction)
    rightMenu.addAction(copyAction)
    rightMenu.addAction(pasteAction)
    rightMenu.addAction(disperseCellsAction)

    rightMenu.exec_(pos)

Ui_MainWindow.rightMenuShow = rightMenuShow


if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        myapp = Ui_MainWindow()

        myapp.setupUi(window)

        window.show()
        sys.exit(app.exec_())