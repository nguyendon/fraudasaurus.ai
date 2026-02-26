import { ImageResponse } from "next/og";

export const size = {
  width: 180,
  height: 180,
};
export const contentType = "image/png";

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#222034",
          borderRadius: 32,
        }}
      >
        {/* Scaled pixel T-Rex head for Apple touch icon */}
        <svg
          viewBox="0 0 32 32"
          width="140"
          height="140"
          style={{ imageRendering: "pixelated" }}
        >
          <rect x="4" y="20" width="4" height="4" fill="#6abe30" />
          <rect x="8" y="16" width="4" height="8" fill="#6abe30" />
          <rect x="12" y="12" width="4" height="12" fill="#6abe30" />
          <rect x="16" y="8" width="8" height="12" fill="#6abe30" />
          <rect x="24" y="8" width="4" height="8" fill="#6abe30" />
          {/* Eye */}
          <rect x="24" y="10" width="2" height="2" fill="#cbdbfc" />
          {/* Jaw */}
          <rect x="20" y="18" width="8" height="4" fill="#6abe30" />
          {/* Teeth */}
          <rect x="22" y="16" width="2" height="2" fill="#cbdbfc" />
          <rect x="26" y="16" width="2" height="2" fill="#cbdbfc" />
        </svg>
      </div>
    ),
    {
      ...size,
    }
  );
}
