# os
import os

# argument parsing helper
import fire

# good ol' numpy
import numpy as np

# geometry helpers
from compas.geometry import subtract_vectors
from compas.geometry import length_vector_sqrd

# these are custom-written functions part of this library
# which you can find in the src/directional_clustering folder

#JSON file directory
from directional_clustering import JSON

# extended version of Mesh
from directional_clustering.mesh import MeshPlus

# clustering algorithms factory
from directional_clustering.clustering import ClusteringFactory

# vector field
from directional_clustering.fields import VectorField

# transformations
from directional_clustering.transformations import align_vector_field
from directional_clustering.transformations import smoothen_vector_field

#plotters
from directional_clustering.plotters import PlyPlotter


# ==============================================================================
# Main function: directional_clustering
# ==============================================================================

def directional_clustering(filename="perimeter_supported_slab",
                           align_vectors=True,
                           alignment_ref=[1.0, 0.0, 0.0],
                           smooth_iters=10,
                           damping=0.5,
                           clustering_name="variational kmeans",
                           n_clusters=5,
                           tol=1e-6,
                           iters=30,
                           export_json=True):
    """
    Cluster a vector field atop a mesh based on its direction.

    Parameters
    ----------
    filename : `str`
        The name of the JSON file that encodes a mesh.
        \nAll JSON files must reside in this repo's data/json folder.
        Defaults to "perimeter_supported_slab".

    align_vectors : `bool`
        Flag to align vectors relative to a reference vector.
        \nDefaults to False.

    alignment_ref : `list` of `float`
        The reference vector for alignment.
        \nDefaults to [1.0, 0.0, 0.0].

    smooth_iters : `int`
        The number iterations of Laplacian smoothing on the vector field.
        \nIf set to 0, no smoothing will take place.
        Defaults to 10.

    damping : `float`
        A value between 0.0 and 1.0 to control the intensity of the smoothing.
        \nZero technically means no smoothing. One means maximum smoothing.
        Defaults to 0.5.

    clustering_name : `str`
        The name of the algorithm to cluster the vector field.
        \nSupported options are `cosine kmeans` and `variational kmeans`.
        Defaults to `cosine kmeans`.

    n_clusters : `int`
        The number of clusters to generate.
        \nDefaults to 5.

    iters : `int`
        The number of iterations to run the clustering algorithm for.
        \nDefaults to 30.

    tol : `float`
        A small threshold value that marks clustering convergence.
        \nDefaults to 1e-6.

    export_json: `bool`
        True to export the vector field and the mesh to JSON file.
        \nDefaults to True.
    """

    # ==============================================================================
    # Set directory of input JSON files
    # ==============================================================================

    # Relative path to the JSON file stores the vector fields and the mesh info
    # The JSON files must be stored in the data/json_files folder

    name_in = filename + ".json"
    json_in = os.path.abspath(os.path.join(JSON, name_in)) 

    # ==============================================================================
    # Import a mesh as an instance of MeshPlus
    # ==============================================================================

    mesh = MeshPlus.from_json(json_in)

    # ==============================================================================
    # Search for supported vector field attributes and take one choice from user
    # ==============================================================================
    
    # supported vector field attributes
    supported_attr = mesh.vector_fields()
    print("supported vector field attributes are:\n", supported_attr)
    
    # vectorfield_tag : The name of the vector field to cluster.
    vectorfield_tag = input("please choose one attribute:")

    # ==============================================================================
    # Extract vector field from mesh for clustering
    # ==============================================================================

    vectors = mesh.vector_field(vectorfield_tag)

    # ==============================================================================
    # Align vector field to a reference vector
    # ==============================================================================

    # the output of the FEA creates vector fields that are oddly oriented.
    # Eventually, what we want is to create "lines" from this vector
    # field that can be materialized into reinforcement bars, beams, or pipes which
    # do not really care about where the vectors are pointing to.
    # concretely, a vector can be pointing to [1, 1] or to [-1, 1] but for archi-
    # tectural and structural reasons this would be the same, because both versions
    # are colinear.
    #
    # in short, mitigating directional duplicity is something we are kind of
    # sorting out with a heuristic. this will eventually improve the quality of the
    # clustering
    #
    # how to pick the reference vector is arbitrary ("user-defined") and something
    # where there's more work to be done on. in the meantime, i've used the global
    # x and global y vectors as references, which have worked ok for my purposes.

    if align_vectors:
        align_vector_field(vectors, alignment_ref)

    # ==============================================================================
    # Apply smoothing to the vector field
    # ==============================================================================

    # moreover, depending on the quality of the initial mesh, the FEA-produced
    # vector field will be very noisy, especially around "singularities".
    # this means there can be drastic orientation jumps/flips between two vectors
    # which will affect the quality of the clustering.
    # to mitigate this, we apply laplacian smoothing which helps to soften and 
    # preserve continuity between adjacent vectors
    # what this basically does is going through every face in the mesh,
    # querying what are their neighbor faces, and then averaging the vectors stored
    # on each of them to finally average them all together. the "intensity" of this
    # operation is controlled with the number of smoothing iterations and the
    # damping coefficient.
    # too much smoothing however, will actually distort the initial field to the
    # point that is not longer "representing" the original vector field
    # so smoothing is something to use with care

    if smooth_iters:
        smoothen_vector_field(vectors, mesh.face_adjacency(), smooth_iters, damping)
        #smoothened_field_name = vectorfield_tag + "_smoothened"
        #mesh.vector_field(smoothened_field_name, vectors)

    # ==============================================================================
    # Do K-means Clustering
    # ==============================================================================

    # now we need to put the vector field into numpy arrays to carry out clustering
    # current limitation: at the moment this only works in planar 2d meshes!
    # other clustering methods, like variational clustering, can help working
    # directly on 3d by leveraging the mesh datastructure
    # other ideas relate to actually "reparametrizing" (squishing) a 3d mesh into a
    # 2d mesh, carrying out clustering directly in 2d, and then reconstructing
    # the results back into the 3d mesh ("reparametrizing it back")

    # One of the key differences of this work is that use cosine distance as
    # basis metric for clustering. this is in constrast to numpy/scipy
    # whose implementations, as far as I remember support other types of distances
    # like euclidean or manhattan in their Kmeans implementations. this would not
    # work for the vector fields used here, but maybe this has changed now.
    # in any case, this "limitation" led me to write our own version of kmeans
    # which can do clustering based either on cosine or euclidean similarity

    # kmeans is sensitive to initialization
    # there are a bunch of approaches that go around it, like kmeans++
    # i use here another heuristic which iteratively to find the initial seeds
    # using a furthest point strategy, which basically picks as a new seed the
    # vector which is the "most distant" at a given iteration using kmeans itself
    # These seeds will be used later on as input to start the final kmeans run.
    
    print("Clustering started...")

    # Create an instance of a clustering algorithm from ClusteringFactory
    clustering_algo = ClusteringFactory.create(clustering_name)
    clusterer = clustering_algo(mesh, vectors, n_clusters, iters, tol)

    # do kmeans clustering
    # labels contains the cluster index assigned to every vector in the vector field
    # centers contains the centroid of every cluster (the average of all vectors in
    # a cluster), and losses stores the losses generated per epoch.
    # the loss is simply the mean squared error of the cosine distance between
    # every vector and the centroid of the cluster it is assigned to
    # the goal of kmeans is to minimize this loss function

    clusterer.cluster()

    print("Loss Clustering: {}".format(clusterer.loss))
    print("Clustering ended!")

    # store results in clustered_field and labels
    clustered_field = clusterer.clustered_field
    labels = clusterer.labels
    
    # ==============================================================================
    # Compute mean squared error "loss" of clustering
    # ==============================================================================

    # probably would be better to encapsulate this in a function or in a Loss object
    # clustering_error = MeanSquaredError(vector_field, clustered_field)
    # clustering_error = MeanAbsoluteError(vector_field, clustered_field)

    errors = np.zeros(mesh.number_of_faces())
    for fkey in mesh.faces():
        # for every face compute difference between clustering output and
        # aligned+smoothed vector, might be better to compare against the
        # raw vector
        difference_vector = subtract_vectors(clustered_field.vector(fkey),
                                             vectors.vector(fkey))
        errors[fkey] = length_vector_sqrd(difference_vector)

    mse = np.mean(errors)

    print("Clustered Field MSE: {}".format(mse))

    # ==============================================================================
    # Assign clusters back to mesh
    # ==============================================================================

    # add the clustered vector field and label with correspondding attibutes to mesh
    
    # name for storage
    clustered_field_name = vectorfield_tag + "_clustered"
    mesh.vector_field(clustered_field_name, clustered_field)

    mesh.clustering_label("cluster", labels)
    
    # ==============================================================================
    # Export new JSON file for further processing
    # ==============================================================================

    if export_json:
        name_out = filename + "_" + vectorfield_tag+ "_{}_{}.json".format(clustering_name, 
                    n_clusters)
        json_out = os.path.abspath(os.path.join(JSON, name_out))
        mesh.to_json(json_out)
        print("Exported clustered mesh to: {}".format(json_out))
    
if __name__ == '__main__':
    fire.Fire(directional_clustering)
