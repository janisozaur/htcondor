#! /usr/bin/env perl

$retry = $ARGV[0];
if ($retry gt 0) {
	print "POST script succeeds\n";
	close(OUT);
} else {
	print "POST script fails\n";
	exit 1;
}
