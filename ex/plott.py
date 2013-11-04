# this file is a wrapper for matplotlib so that it feels more like
# matlab. some enhancements are also added.

from ex.common import *

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D

from matplotlib.pyplot import plot, semilogx, semilogy, loglog, scatter, legend, hist, errorbar, arrow, axis, text, show, draw, gca, gcf, cla, title, xlim, ylim

def figure(show = True):
    fig = plt.figure()
    if show: fig.show()
    return fig

def subplot(fig, position):
    return fig.add_subplot(position)

def plot3(fig, xs, ys, zs, *args, **kwargs):
    ax = Axes3D(fig)
    ax.plot(xs, ys, zs, *args, **kwargs)

def scatter3(fig, xs, ys, zs, *args, **kwargs):
    ax = Axes3D(fig)
    ax.scatter(xs, ys, zs, 'z', *args, **kwargs)

def sca(h):
    '''set current axes
    '''

    plt.axes(h)

def scf(h):
    '''set current figure
    '''

    plt.figure(h.number)

def ErrorBarX(x, ys, bar = 'std', *args, **kwargs):
    '''plot errorbar graph for random run data. 

    each row of ys if one run
    '''

    if bar == 'std':
        return errorbar(x, ys.mean(0), ys.std(0, ddof = 1), *args, **kwargs)
    elif bar == 'range':
        ymean = ys.mean(0)
        return errorbar(x, ymean, (ymean - ys.min(0), ys.max(0) - ymean), 
                 *args, **kwargs)
    else:
        raise ValueError('unknown bar type')

def CompareVectors(ref, v):
    '''compare two vectors
    '''

    n = len(ref)
    idx = np.argsort(ref)
    ref = ref[idx]
    v = v[idx]

    plot(np.arange(n), ref, 'b', np.arange(n), v, 'r')

if __name__ == '__main__':
    fig = figure()
    subplot(fig, 121)
    for i in range(12):
        cla()
        title('Test plot')
        plot(np.arange(-10, i), np.arange(-10, i)**2)
        draw()

    subplot(fig, 122)
    title('Test scatter')
    scatter(np.arange(-10, 11), np.arange(-10, 11)**2)
    text(5, 0, 'haha')
    draw()

    fig3d=figure()
    z = np.linspace(-2, 2, 100)
    r = z**2 + 1
    theta = np.linspace(-4 * np.pi, 4 * np.pi, 100)
    x = r * np.sin(theta)
    y = r * np.cos(theta)

    # plot3(fig3d, x, y, z, label='test curve')
    # draw()
    # pause()

    scatter3(fig3d, x, y, z)
    draw()

    show()
