from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="drone-e99-face-recognition",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Real-time face recognition and anti-spoofing system for drone and webcam",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/drone_e99_face_recognition",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "drone-face-rec=main:main",
            "drone-enroll-image=tools.enroll_image:main",
            "drone-enroll-video=tools.enroll_video:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.onnx"],
    },
)