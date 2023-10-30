import torch
import torch.nn as nn
import dgl.nn as dglnn
import dgl.function as fn

class GraphConvLayer(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(GraphConvLayer, self).__init__()

        # Graph convolution operation
        self.graph_conv = dglnn.GraphConv(input_dim, output_dim, norm='both', weight=True)
        
    def forward(self, graph):
        # Apply the graph convolution operation
        graph.ndata['h'] = self.graph_conv(graph, graph.ndata['h'])
        return graph
    
def create_classification_model(input_dim, hidden_dim, output_dim):
    # Graph Convolutional Layer
    layers = [
        GraphConvLayer(input_dim, hidden_dim),
        nn.Linear(hidden_dim, output_dim)
    ]
    model = nn.Sequential(*layers)
    return model





