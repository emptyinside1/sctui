{ pkgs ? import <nixpkgs> {} }:

let
  pythonPackages = pkgs.python3Packages;
  native-deps = with pkgs; [ mpv ffmpeg ];
in
pkgs.mkShell {
  buildInputs = [
    (pkgs.python3.withPackages (ps: with ps; [
      textual
      yt-dlp
      python-mpv
      platformdirs
    ]))
  ] ++ native-deps;

  LD_LIBRARY_PATH = "${pkgs.lib.makeLibraryPath native-deps}";
}
