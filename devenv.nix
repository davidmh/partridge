{ pkgs, ... }:

{
  devenv.warnOnNewVersion = false;

  languages.python = {
    enable = true;
    uv.enable = true;
  };

  packages = with pkgs; [
    graphviz # Provides the dot command to build the dependency graph
  ];
}
