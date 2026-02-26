import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Fraudasaurus",
    short_name: "Fraudasaurus",
    description: "Fraud detection for the digital age",
    start_url: "/",
    display: "standalone",
    background_color: "#222034",
    theme_color: "#222034",
    icons: [
      {
        src: "/icon",
        sizes: "32x32",
        type: "image/png",
      },
      {
        src: "/icon-192",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icon-512",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
