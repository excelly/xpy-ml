from ex.plott import *
from common import *

class PCA:
    '''wrapper for PCA related computations
    '''

    def __init__(self, filename = None):
        '''Fields:
        n: training samples.
        dim: training dimensions.
        U: principle components.
        L: eigen values.
        M: training mean.
        R: effective dim.
        E: energy preserved by R
        '''

        if filename is None:
            self.n, self.dim, self.U, self.L, self.M, self.R, self.E = [None]*7
        else:
            self.Load(filename)

    @staticmethod
    def Train(X, E = 0.99, method = None):
        '''train the model from the design matrix

        method can be 'cov' for 'gram'
        '''

        X = float64(X)
        model = PCA()

        model.n, model.dim = X.shape
        model.R = min(model.dim, model.n)

        model.M = X.mean(0)
        X = X - model.M

        if (method is None and model.n >= model.dim) or (method == 'cov'):
            log.info('Training PCA using COV method')

            C = mul(X.T, X)*(1.0/model.n)
            model = PCA.TrainCov(model.M, C, model.n, E)
        elif (method is None and model.n < model.dim) or (method == 'gram'):
            log.info('Training PCA using GRAM method')

            Grm = mul(X, X.T)
            model.L, V = eigh(Grm*(1./n))
            sidx = argsort(model.L)[::-1]
            sidx = sidx[:min(model.n, model.dim)]
            model.L = model.L[sidx]
            model.U = mul(X.T, V[:, sidx])*(1.0/sqrt(model.L))

            model.U = Normalize(model.U, 'n1', 'col')[0]
            model.R = EffRank(model.L, E)
            model.E = E
        else:
            raise ValueError('unknown method')

        log.info(model)
        return model

    @staticmethod
    def TrainCov(M, Cov, N, E = 0.95):
        '''train the model using prepared mean and covariance
        
        the Cov should be cX'*cX/n, cX is the centered X
        '''

        model = PCA()

        model.n = N
        model.dim = len(M)

        model.M = M.ravel()
        model.L, U = eigh(Cov)
        sidx = argsort(model.L)[::-1]
        model.L = model.L[sidx]
        model.U = U[:, sidx]

        model.U = Normalize(model.U, 'n1', 'col')[0]
        model.R = EffRank(model.L, E)
        model.E = E

        return model

    def AdjustDim(self, E):
        '''adjust the effective dimensionality to preserve E energy
        '''

        self.R = self.EffRank(self.L, E)

    def Project(self, X, dims = None):
        '''project X onto the principle components.
        X and result will be one sample per row.
        '''

        if dims is None: dims = arange(self.R)
        return mul(X - self.M, self.U[:, dims])

    def Visualize(self, X, y='b', dim=2):
        '''embed X into a low-dimensional space
        y is used to color points
        '''

        if dim == 2:
            P = self.Project(X, arr([0,1]))
            scatter(P[:,0], P[:,1], c = y, edgecolors='none')
            draw()
        else:
            raise ValueError('only 2D plot is supported')

    def Reconstruct(self, Y):
        '''reconstruct the project data. one sample per row.
        '''

        r=Y.shape[1]
        return shift(mul(Y, self.U[:, :r].T), self.M, 0)

    def Save(self, filename):
        '''save this model to file
        '''

        format=filename.split('.')[-1].lower()
        check(format in ['pkl','mat'], 'unknown file format')

        if format == 'pkl':
            SavePickle(filename, self)
        else:
            SaveMat(filename, self.__dict__)

    def Load(self, filename):
        '''load a model from file
        '''

        format = SplitFilename(filename)[-1].lower()
        check(format in ['pkl','mat'], 'unknown file format')

        if format == 'pkl':
            o = LoadPickles(filename)
            CopyAtt(o, self)
        else:
            data = LoadMat(filename)
            CopyAtt(data, self)

    def __str__(self):
        return 'PCA model. Trained from {0} samples of dim {1}. Effective Dim = {2} preserving {3:.3}% energy'.format(
            self.n, self.dim, self.R, self.E*100)

    def Plot(self):
        '''plot a summary of current model
        '''
        
        fig=figure()
        subplot(fig, 121)
        plot(self.M)
        title('Mean')
        subplot(fig, 122)
        semilogy(self.L)
        title('L')
        draw()

if __name__ == '__main__':
    InitLog()

    from gmm import GMM
    gmm = GMM(arr([1, 1, 1]), arr([[0., -1.], [0, 1], [1, -2]]), eye(2)*3e-2)
    n = 1000
    X, y = gmm.GenData(n)
    
    figure()
    subplot(gcf(), 121)
    model = PCA.Train(X, method='cov')
    model.Visualize(X, y)
    print model.L

    subplot(gcf(), 122)
    model = PCA.Train(X, method='gram')
    model.Visualize(X, y)
    print model.L

    draw()
