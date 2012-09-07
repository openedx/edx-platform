Feature: Scrape a textbook
  In order to scrape a textbook
  As a registered user
  We'll attempt to create local html copies of the text

  Scenario: Get the book
  	Given I visit "http://students.flatworldknowledge.com/bookhub/reader/4309"
  	I scrape the page
  	
