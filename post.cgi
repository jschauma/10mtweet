#! /usr/pkg/bin/perl -Tw
#
# This simple CGI script is used to post and then schedule the deletion of
# a tweet.  This is done by using the tweet(1) command found at
# https://github.com/jschauma/tweet in combination with at(8).
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

my $ACCOUNT = "10mtweet";
my $AT = "at now + 10 minutes >/dev/null 2>&1";
my $TWEET_CMD = "/home/jschauma/bin/tweet -c /home/jschauma/.tweetrc-10mtweet -u $ACCOUNT";
my $TWEET = "$TWEET_CMD -i -t";

delete($ENV{'REMOTE_ADDR'});
delete($ENV{'HTTP_USER_AGENT'});
$ENV{'PATH'} = '/bin:/usr/bin:/usr/pkg/bin';

print "Content-Type: text/html\n\n";

###
### Functions
###

sub callback($) {
	my ($uri) = @_;
	my $host = $uri->host;
	my $undotted = $host;
	$undotted =~ s/(.*)\.(.*)$/$1 $2/;
	$uri =~ s/https?:\/\///g;
	$uri =~ s/$host/$undotted/;
	return $uri;
}

sub cleanMsg($) {
	my ($msg) = @_;

	$msg =~ s/\+/ /g;
	$msg =~ s/%(..)/pack('c',hex($1))/eg;
	$msg =~ s/@(\S)/$1/g;

	my $finder = URI::Find::Schemeless->new(\&callback);
	$finder->find(\$msg);

	return $msg;
}

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

sub scheduleDeletion($) {
	my ($id) = @_;
	open(P, "| $AT") or error("Unable to schedule tweet for deletion.");
	print P "$TWEET -d $id";
	close(P);

	my $intenminutes = strftime("%Y-%m-%d %H:%M %z", localtime(time() + 600));
	print <<EOM
	<p>
	  <a href="https://twitter.com/$ACCOUNT/status/$id">This tweet</a> is scheduled for deletion at approximately: $intenminutes
	</p>
EOM
;
}

sub tweet($) {
	my ($msg) = @_;
	my ($id, $pid, @errors);
	my @command = split(/\s+/, $TWEET);

	$pid = open3(\*WH, \*RH, \*EH, @command);
	print WH "$msg\n";
	close(WH);

	while (my $l = <EH>) {
		chomp($l);
		push(@errors, $l);
	}
	close(EH);

	if (@errors) {
		error(join(" ", @errors));
	}

	while (my $l = <RH>) {
		chomp($l);
		$id = $l;
	}
	waitpid($pid, 0);

	if (!$id) {
		error("Unable to tweet, sorry.");
	}

	print <<EOH
  <P>
	Alright, <a href="https://twitter.com/$ACCOUNT/status/$id">tweet</a> sent.
  </P>
EOH
;
	return $id;
}

sub printFoot() {
	print <<EOH
  <HR>
  <a href="/">Back to 10 Minute Tweet</a>
  </BODY>
</HTML>
EOH
;
}

sub printHead() {
	print <<EOH
<HTML>
  <HEAD>
    <TITLE>10 Minute Tweet</TITLE>
  </HEAD>
  <BODY>
  <H1>10 Minute Tweet</H1>
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
	$value = cleanMsg($value);
	$tweet = tweet($value);
	scheduleDeletion($tweet);
}
printFoot();
