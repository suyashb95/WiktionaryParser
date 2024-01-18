import torch
import torch.nn as nn
import dgl.nn as dglnn
import dgl.function as fn


# Create a custom graph convolutional layer
class CustomGraphConvLayer(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(CustomGraphConvLayer, self).__init__()

        # Graph convolution operation
        self.graph_conv = dglnn.GraphConv(input_dim, output_dim, norm='both', weight=True)

    def forward(self, g, feats):
        # Apply the graph convolution operation
        attr = "h"
        g.ndata[attr] = self.graph_conv(g, feats)
        # Perform edge classification (e.g., binary classification)
        
        edge_features = g.edata['feat']  # Replace 'feat' with the name of your edge features
        edge_scores = self.out(edge_features)

        return edge_scores
        

def create_combined_model(input_dim, hidden_dim, output_dim):
    # Create an nn.Sequential model with a combination of layers
    model = nn.Sequential(
        CustomGraphConvLayer(input_dim, hidden_dim),  # Custom graph convolutional layer
        nn.Linear(hidden_dim, output_dim)  # PyTorch linear layer
    )

    return model


