package com.example.demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;

@SpringBootApplication
@RestController
public class DemoApplication {

	public static void main(String[] args) {

		SpringApplication.run(DemoApplication.class, args);
	}

	private List<User> userList = new ArrayList<>();
	private AtomicInteger idCounter = new AtomicInteger(1);

// add user
	@PostMapping("/addUser")
	public String addUser(@RequestBody User user) {
		user.setId(idCounter.getAndIncrement());
		userList.add(user);
		return "User added: ID = " + user.getId() + ", Name = " + user.getName();
	}
// show all added users
	@GetMapping("/users")
	public List<User> getAllUsers() {
		return userList;
	}

// show user by ID
	@GetMapping("/users/{id}")
	public User getUserById(@PathVariable int id) {
		Optional<User> user = userList.stream()
				.filter(u -> u.getId() == id)
				.findFirst();

		return user.orElse(null);
	}

// test
//	@GetMapping("/hello")
//	public String hello(@RequestParam(value = "name", defaultValue = "World") String name) {
//		return String.format("Hello %s!", name);
//	}
}
