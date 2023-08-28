from sklearn.cluster import KMeans
import cv2
class ImageDetector:

    def __init__(self, **kwargs):
        ...

    def set_image(self, path):
        self.image = cv2.imread(path)
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.pixels = self.image.reshape((-1, 3))

    def cluster_image(self, n_clusters):
        self.kmeans = KMeans(n_clusters=n_clusters)

    def get_color_match(self):
        self.kmeans.fit(self.pixels)
        colors = self.kmeans.cluster_centers_

        dominant_colors = colors.round(0).astype(int)
