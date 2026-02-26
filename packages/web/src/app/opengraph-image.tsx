import { ImageResponse } from "next/og";

export const runtime = "edge";

export const alt = "Fraudasaurus - Fraud Detection for the Digital Age";
export const size = {
  width: 1200,
  height: 630,
};
export const contentType = "image/png";

export default async function Image() {
  // Load Press Start 2P font (TTF format required for OG images)
  const pressStart2P = await fetch(
    "https://github.com/google/fonts/raw/main/ofl/pressstart2p/PressStart2P-Regular.ttf"
  ).then((res) => res.arrayBuffer());

  return new ImageResponse(
    (
      <div
        style={{
          background: "#222034",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: '"Press Start 2P"',
          position: "relative",
        }}
      >
        {/* Grid pattern overlay */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundImage:
              "linear-gradient(#2a2848 1px, transparent 1px), linear-gradient(90deg, #2a2848 1px, transparent 1px)",
            backgroundSize: "40px 40px",
            opacity: 0.5,
          }}
        />

        {/* Corner accents - top left */}
        <div
          style={{
            position: "absolute",
            top: 30,
            left: 30,
            width: 60,
            height: 8,
            background: "#d95763",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: 30,
            left: 30,
            width: 8,
            height: 60,
            background: "#d95763",
          }}
        />

        {/* Corner accents - top right */}
        <div
          style={{
            position: "absolute",
            top: 30,
            right: 30,
            width: 60,
            height: 8,
            background: "#5fcde4",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: 30,
            right: 30,
            width: 8,
            height: 60,
            background: "#5fcde4",
          }}
        />

        {/* Corner accents - bottom left */}
        <div
          style={{
            position: "absolute",
            bottom: 30,
            left: 30,
            width: 60,
            height: 8,
            background: "#5fcde4",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: 30,
            left: 30,
            width: 8,
            height: 60,
            background: "#5fcde4",
          }}
        />

        {/* Corner accents - bottom right */}
        <div
          style={{
            position: "absolute",
            bottom: 30,
            right: 30,
            width: 60,
            height: 8,
            background: "#d95763",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: 30,
            right: 30,
            width: 8,
            height: 60,
            background: "#d95763",
          }}
        />

        {/* Main title */}
        <div
          style={{
            fontSize: 64,
            color: "#d95763",
            textShadow: "4px 4px 0 #141020",
          }}
        >
          FRAUDASAURUS
        </div>

        {/* Subtitle */}
        <div
          style={{
            fontSize: 20,
            color: "#5fcde4",
            marginTop: 32,
            textTransform: "uppercase",
          }}
        >
          Fraud Detection for the Digital Age
        </div>

        {/* Decorative pixels - left */}
        <div
          style={{
            position: "absolute",
            bottom: 150,
            left: 200,
            display: "flex",
            gap: 8,
            opacity: 0.6,
          }}
        >
          <div style={{ width: 12, height: 12, background: "#d95763" }} />
          <div
            style={{
              width: 12,
              height: 12,
              background: "#d95763",
              marginTop: 20,
            }}
          />
          <div style={{ width: 12, height: 12, background: "#d95763" }} />
        </div>

        {/* Decorative pixels - right */}
        <div
          style={{
            position: "absolute",
            bottom: 150,
            right: 200,
            display: "flex",
            gap: 8,
            opacity: 0.6,
          }}
        >
          <div style={{ width: 12, height: 12, background: "#5fcde4" }} />
          <div
            style={{
              width: 12,
              height: 12,
              background: "#5fcde4",
              marginTop: 20,
            }}
          />
          <div style={{ width: 12, height: 12, background: "#5fcde4" }} />
        </div>

        {/* Bottom tagline */}
        <div
          style={{
            position: "absolute",
            bottom: 50,
            fontSize: 12,
            color: "#cbdbfc",
            opacity: 0.6,
          }}
        >
          Jack Henry DevCon 2026
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        {
          name: "Press Start 2P",
          data: pressStart2P,
          style: "normal",
          weight: 400,
        },
      ],
    }
  );
}
