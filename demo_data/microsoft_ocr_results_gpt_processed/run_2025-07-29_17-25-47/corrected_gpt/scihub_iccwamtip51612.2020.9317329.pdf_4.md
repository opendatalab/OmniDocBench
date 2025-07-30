Table 4 Comparison review with existing work's methods and accuracy scores.

| Method          | Data set     | Subject | F1 Score | Modality          | Training Accuracy | Validation Accuracy |
|-----------------|--------------|---------|----------|-------------------|-------------------|---------------------|
| SVM EBF [18]    | CASIA        | 75      | 0.890    | RGB               | 0.90              | 0.89                |
| Spoof ResNet [19]| MSU-MFSD    | 35      | N/A      | RGB               | 0.978             | 0.944               |
| MTCNN [20]      | YOUTU        | 3350    | 0.956    | RGB/IR            | 0.962             | 0.978               |
| SqueezeNet [21] | CASIA-SURF   | 1000    | N/A      | Color, Depth & IR | N/A               | 0.998               |
| FusionNet       | CASIA-SURF   | 300     | 0.998    | Color, Depth & IR | 0.997             | 0.998               |

# 4. Conclusion

In this research, we used a deep learning method focused on Fusion CNN architecture to derive facial patches and depth of 3 types of human facial image samples, namely Color, Depth, and IR from the CASIA-SURF dataset modeled with an altered 3D convolutional neural network classifier. Our primary interest was to be able to extract facial patches and the depth levels of all 3 facial inputs stated earlier to distinguish a real face from a spoofed face from the CASIA-SURF dataset provided, which are not preprocessed.

## Acknowledgements

This work is supported by the Department of Science and Technology of Sichuan Province, China, under Grant 2019YJ0166.

## References

[1] J. Berry and D. A. Stoney. The history and development of fingerprinting [J]. Advances in fingerprint Technology, 2001, 2:13-52.

[2] W. Yang, S. Wang, J. Hu, et al. Security and accuracy of fingerprint-based biometrics: A review [J]. Symmetry, 2019, 11(2):141.

[3] L. Introna and H. Nissenbaum. Facial recognition technology: a survey of policy and implementation issues [J]. 2010.

[4] D. Wen, H. Han, and A. K. Jain. Face spoof detection with image distortion analysis [J]. IEEE Transactions on Information Forensics and Security, 2015, 10(4):746-761.

[5] K. A. Nixon, V. Aimale, and R. K. Rowe. Handbook of biometrics, 2008, 403-423.

[6] A. da Silva Pinto, H. Pedrini, W. Schwartz, et al. Video-based face spoofing detection through visual rhythm analysis [C]. 2012 25th SIBGRAPI Conference on Graphics, Patterns and Images, 2012, 221-228.

[7] A. Krizhevsky, I. Sutskever, and G. E. Hinton. Imagenet classification with deep convolutional neural networks [C]. Advances in neural information processing systems, 2012, 1097-1105.

[8] Y. Atoum, Y. Liu, A. Jourabloo, et al. Face anti-spoofing using patch and depth-based CNNs [C]. 2017 IEEE International Joint Conference on Biometrics (IJCB), 2017, 319-328.

[9] R. Min, J. Choi, G. Medioni, et al. Real-time 3D face identification from a depth camera [C]. Proceedings of the 21st International Conference on Pattern Recognition (ICPR2012), 2012, 1739-1742.

[10] S. Lawrence, C. L. Giles, A. C. Tsoi, et al. Face recognition: A convolutional neural-network approach [J]. IEEE transactions on neural networks, 1997, 8(1):98-113.

[11] Z. Zhang, J. Yan, S. Liu, et al. A face antispoofing database with diverse attacks [C]. 2012 5th IAPR international conference on Biometrics (ICB), 2012, 26-31.

[12] G. Albakri and S. Alghowinem. The effectiveness of depth data in liveness face authentication using 3D sensor cameras [J]. Sensors, 2019, 19(8):1928.

[13] J. Dai, Y. Li, K. He, et al. R-fcn: Object detection via region-based fully convolutional networks [C]. Advances in neural information processing systems, 2016, 379-387.

[14] C.-L. Zhang, J.-H. Luo, X.-S. Wei, et al. In defense of fully connected layers in visual representation transfer [C]. Pacific Rim Conference on Multimedia, 2017, 807-817.

[15] J. Konečny, J. Liu, P. Richtárik, et al. Mini-batch semi-stochastic gradient descent in the proximal setting [J]. IEEE Journal of Selected Topics in Signal Processing, 2015, 10(2):242-255.

[16] A. F. Agarap. Deep learning using rectified linear units (relu) [J]. arXiv preprint arXiv:1803.08375, 2018.

[17] L. Bottou. Neural networks: Tricks of the trade, 2012, 421-436.

[18] M. Hardt, B. Recht, and Y. Singer. Train faster, generalize better: Stability of stochastic gradient descent [J]. arXiv preprint arXiv:1509.01240, 2015.

[19] D. T. van der Haar. Face Antispoofing Using Shearlets: An Empirical Study [J]. SAIEE Africa Research Journal, 2019, 110(2):94-103.

[20] C. Nagpal and S. R. Dubey. A performance evaluation of convolutional neural networks for face anti-spoofing.

<!-- PageNumber="220" -->
<!-- PageFooter="Authorized licensed use limited to: University of Prince Edward Island. Downloaded on June 07, 2021 at 19:31:02 UTC from IEEE Xplore. Restrictions apply." -->