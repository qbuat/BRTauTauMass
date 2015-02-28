# python imports
import os
# ROOT/rootpy 
from ROOT import TMVA
from rootpy.io import root_open
from rootpy.tree import Cut
# local imports
from . import log; log[__name__]
from .variables import VARIABLES
from samples import Higgs
from samples.db import get_file



class Regressor(TMVA.Factory):
    """
    """
    def __init__(self,
                 output_name,
                 features,
                 factory_name='TMVARegression',
                 verbose='V:!Silent:Color:DrawProgressBar'):

        self.output = root_open(output_name, 'recreate')
        TMVA.Factory.__init__(
            self, factory_name, self.output, verbose)
        self.factory_name = factory_name
        self.features = features

    def set_variables(self):
        """
        Set TMVA formated variables
        from the VARIABLES dict (see variables.py)
        """
        for varName in self.features:
            var = VARIABLES[varName]
            self.AddVariable(
                var['name'], 
                var['root'], 
                var['units'] if 'units' in var.keys() else '',
                var['type'])

    def book_brt(self,
                 ntrees=100,
                 node_size=5,
                 depth=8):
        """
        Book the BRT method (set all the parameters)
        """
        params = ["SeparationType=RegressionVariance"]
        params += ["BoostType=AdaBoostR2"]
        params += ["AdaBoostBeta=0.2"]
        params += ["MaxDepth={0}".format(depth)]
        params += ["MinNodeSize={0}%".format(node_size)]
        params += ["NTrees={0}".format(ntrees)]
        # Do we need those or not ?
        # params += ["PruneMethod=NoPruning"]
        # params += ["UseYesNoLeaf=False"]
        # params += ["DoBoostMonitor"]
        # params += ["nCuts={0}".format(nCuts)]
        # params += ["NNodesMax={0}".format(NNodesMax)]
        # DEPRECATED DEPRECATED
        # params += ["nEventsMin={0}".format(nEventsMin)]
        log.info(params)

        method_name = "BRT_HiggsMass"
        params_string = "!H:V"
        for param in params:
            params_string+= ":"+param
        self.BookMethod(
            TMVA.Types.kBDT,
            method_name,
            params_string)

    def train(self, **kwargs):
        """
        Run, Run !
        """
        self.set_variables()
        

        higgs_array = Higgs(mode='VBF', masses=Higgs.MASSES, suffix='_train')

        cut = Cut('hadhad==1')
        
        params = ['nTrain_Regression=0']
        params += ['nTest_Regression=1']
        params += ['SplitMode=Random']
        params += ['NormMode=NumEvents']
        params += ['!V']
        params = ':'.join(params)

        self.PrepareTrainingAndTestTree(cut, params)
        for s in higgs_array.components:
            rfile = get_file(s.ntuple_path, s.student, suffix=s.suffix)
            tree = rfile[s.tree_name]
            self.AddRegressionTree(tree)
        self.AddRegressionTarget('higgs_m')
        # Could reweight samples 
        # self.AddWeightExpression("my_expression")

        # Actual training
        self.book_brt(**kwargs)
        self.TrainAllMethods()