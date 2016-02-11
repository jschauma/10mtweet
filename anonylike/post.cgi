#! /usr/pkg/bin/perl -Tw
#
# This simple CGI script is used to anonymously like a tweet.
# This is done by using the tweet(1) command found at
# https://github.com/jschauma/tweet and using the 'anonylike' account.
#
# This script also tries to minimize the possibility of abuse by stripping
# @-mentions and URLs from the input.

use warnings;
use strict;
use CGI qw(:standard);
use IPC::Open3;
use POSIX qw(strftime);
use URI::Find::Schemeless;

$CGI::POST_MAX=1024;
$CGI::DISABLE_UPLOADS = 1;

my $ACCOUNT = "anonylike";
my $TWEET_CMD = "/home/jschauma/bin/tweet -c /home/jschauma/.tweetrc-anonylike -u $ACCOUNT -l";

delete($ENV{'REMOTE_ADDR'});
delete($ENV{'HTTP_USER_AGENT'});
$ENV{'PATH'} = '/bin:/usr/bin:/usr/pkg/bin';

print "Content-Type: text/html\n\n";

###
### Functions
###

sub error($) {
	my ($msg) = @_;
	print <<EOE
	<p>
	  <b>Error</b><br>
	  <em>$msg</em>
	</p>
EOE
;
	printFoot();
	exit(0);
}

sub like($) {
	my ($msg) = @_;
	my ($id, $pid, @errors);
	my @command = split(/\s+/, $TWEET_CMD);
	push(@command, $msg);

	system(@command) == 0 or
		error("Unable to execute '" . join(" ", @command) . "': $?");

	print <<EOH
  <P>
	I really liked <a href="https://twitter.com/anonylike/status/$msg">that tweet</a>!
  </P>
EOH
;
}

sub printFoot() {
	print <<EOH
  <HR>
  [<a href="/anonylike">Back to Anonylike</a>]&nbsp;|&nbsp;[<a href="/">Send an anonymous, self-distructing tweet</a>]</a>
  </BODY>
</HTML>
EOH
;
}

sub printHead() {
	print <<EOH
<HTML>
  <HEAD>
    <TITLE>Anonylike - kike a tweet without showing who you are</TITLE>
  </HEAD>
  <BODY>
  <H1>Anonymous Likes *</H1>
  <HR>
EOH
;
}

###
### Main
###

printHead();

$ENV{'REQUEST_METHOD'} =~ tr/a-z/A-Z/;
if ($ENV{'REQUEST_METHOD'} ne "POST") {
	error("Sorry, invalid request method.");
} else {
	my ($buffer, $name, $tweet, $value);
	read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
	($name, $value) = split(/=/, $buffer);
	if ($name ne "msg") {
		error("Invalid form submission.");
	}
	if ($value =~ m/^([0-9]+)$/) {
		like($1);
	} else {
		error("Invalid message.  Tweet ID must be numeric.");
	}
}
printFoot();
